const http = require('http'); // Node.js 기본 HTTP 서버 기능을 가져온다.
const fs = require('fs'); // JSON DB와 업로드 파일을 읽고 쓴다.
const path = require('path'); // 운영체제에 맞는 파일 경로를 조합한다.
const crypto = require('crypto'); // 비밀번호 해시와 무작위 ID·세션 토큰을 생성한다.
const { URL } = require('url'); // 요청 URL의 경로와 쿼리 파라미터를 분석한다.

const ROOT = __dirname; // server.js가 있는 mail 폴더를 기준 경로로 사용한다.
const DATA = path.join(ROOT, 'data'); // JSON 데이터가 저장될 폴더를 계산한다.
const FILES = path.join(DATA, 'files'); // 업로드 파일 저장 폴더를 계산한다.
const DB_PATH = path.join(DATA, 'db.json'); // 사용자·메일·파일 메타데이터 DB 경로를 정한다.
fs.mkdirSync(FILES, { recursive: true }); // 파일 저장 폴더가 없으면 상위 폴더까지 생성한다.

function hash(password, salt = crypto.randomBytes(16).toString('hex')) {
  return { salt, digest: crypto.scryptSync(password, salt, 64).toString('hex') }; // salt와 scrypt 해시를 함께 반환해 평문 비밀번호를 저장하지 않는다.
}
function verify(password, u) { return crypto.timingSafeEqual(Buffer.from(hash(password, u.salt).digest, 'hex'), Buffer.from(u.passwordHash, 'hex')); } // 입력 비밀번호의 해시를 저장 해시와 안전하게 비교한다.
function id(prefix) { return `${prefix}_${crypto.randomBytes(7).toString('hex')}`; } // 파일·메일 등에 충돌 가능성이 낮은 ID를 만든다.
function now() { return new Date().toISOString(); } // 생성·전송 시각을 ISO 문자열로 만든다.
function seed() {
  const admin = hash('admin1234'); const user = hash('user1234'); // 초기 관리자와 일반 사용자 비밀번호를 해시한다.
  return { users: [
    { id:'usr_admin', email:'admin@jewel.cloud', name:'Jewel 관리자', role:'admin', grade:'관리자', passwordHash:admin.digest, salt:admin.salt, blocked:false, settings:{autoFit:true, theme:'light'}, createdAt:now() },
    { id:'usr_demo', email:'user@jewel.cloud', name:'데모 사용자', role:'client', grade:'일반', passwordHash:user.digest, salt:user.salt, blocked:false, settings:{autoFit:true, theme:'light'}, createdAt:now() }
  ], files:[], mails:[
    { id:'mail_welcome', from:'admin@jewel.cloud', to:['user@jewel.cloud'], subject:'Jewel Cloud에 오신 것을 환영합니다', body:'파일과 메일을 한 곳에서 관리해 보세요.', folder:'inbox', read:false, createdAt:now() }
  ], blocks:[], sessions:{} };
}
let db = fs.existsSync(DB_PATH) ? JSON.parse(fs.readFileSync(DB_PATH, 'utf8')) : seed(); // 기존 DB를 읽거나 새 기본 데이터를 만든다.
function save() { fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2)); } // 현재 메모리 DB를 보기 좋은 JSON으로 저장한다.
if (!fs.existsSync(DB_PATH)) save(); // 최초 실행이면 seed 데이터를 파일에 기록한다.

function send(res, code, data, type='application/json') { res.writeHead(code, {'Content-Type':type, 'Access-Control-Allow-Origin':'*'}); res.end(type === 'application/json' ? JSON.stringify(data) : data); } // HTTP 상태·헤더·JSON 또는 파일 응답을 공통 처리한다.
function parseCookies(req) { return Object.fromEntries((req.headers.cookie || '').split(';').filter(Boolean).map(x => x.trim().split('=').map(decodeURIComponent))); } // Cookie 헤더를 키·값 객체로 변환한다.
function safeUser(u) { const {passwordHash, salt, ...safe} = u; return safe; } // 응답에서 비밀번호 해시와 salt를 제거한다.
function auth(req, res, admin=false) {
  const token = parseCookies(req).jewel_session; const uid = token && db.sessions[token]; const u = db.users.find(x => x.id === uid); // 세션 쿠키로 현재 사용자를 찾는다.
  if (!u || u.blocked || (admin && u.role !== 'admin')) { send(res, admin ? 403 : 401, {error:'인증 또는 권한이 필요합니다.'}); return null; } // 미인증·차단·관리자 권한 부족 요청을 거부한다.
  return u; // 인증된 사용자 객체를 API 처리기에 전달한다.
}
function body(req) { return new Promise((resolve,reject) => { let raw=''; req.on('data', c => { raw += c; if (raw.length > 18e6) req.destroy(); }); req.on('end', () => { try { resolve(raw ? JSON.parse(raw) : {}); } catch(e) { reject(e); } }); }); } // 요청 본문을 18MB 이하 JSON으로 읽는다.
function publicFileName(name) { return String(name || 'file').replace(/[^a-zA-Z0-9가-힣._ -]/g, '_').slice(0,120); } // 파일명을 정리해 경로 조작과 과도한 길이를 줄인다.

async function api(req, res, pathname) {
  try {
    if (req.method === 'OPTIONS') return send(res,204,''); // 브라우저 CORS 사전 요청에는 본문 없이 성공을 반환한다.
    if (req.method === 'POST' && pathname === '/api/auth/signup') {
      const b=await body(req); if (!b.email || !b.password || !b.name) return send(res,400,{error:'이름, 이메일, 비밀번호를 입력하세요.'}); // 회원가입 필수값을 검증한다.
      if (db.users.some(u=>u.email.toLowerCase()===b.email.toLowerCase())) return send(res,409,{error:'이미 사용 중인 이메일입니다.'}); // 이메일 중복 가입을 막는다.
      const h=hash(b.password); const u={id:id('usr'),email:b.email.toLowerCase(),name:b.name,role:'client',grade:'일반',passwordHash:h.digest,salt:h.salt,blocked:false,settings:{autoFit:true,theme:'light'},createdAt:now()}; db.users.push(u); save(); return send(res,201,{user:safeUser(u)}); // 신규 일반 사용자를 저장하고 안전한 사용자 정보만 반환한다.
    }
    if (req.method === 'POST' && pathname === '/api/auth/login') {
      const b=await body(req), u=db.users.find(x=>x.email===String(b.email||'').toLowerCase()); // 로그인 입력과 계정을 조회한다.
      if (!u || !verify(String(b.password||''),u) || u.blocked) return send(res,401,{error:'이메일 또는 비밀번호가 올바르지 않습니다.'}); // 계정·비밀번호·차단 상태를 확인한다.
      const token=crypto.randomBytes(32).toString('hex'); db.sessions[token]=u.id; save(); res.setHeader('Set-Cookie',`jewel_session=${token}; HttpOnly; SameSite=Lax; Path=/`); return send(res,200,{user:safeUser(u)}); // 세션 토큰을 저장하고 HttpOnly 쿠키로 발급한다.
    }
    if (req.method === 'POST' && pathname === '/api/auth/logout') { const t=parseCookies(req).jewel_session; delete db.sessions[t]; save(); res.setHeader('Set-Cookie','jewel_session=; Max-Age=0; Path=/'); return send(res,200,{ok:true}); } // 세션을 삭제하고 쿠키를 만료시킨다.
    const u=auth(req,res); if (!u) return; // 인증이 필요한 API를 현재 사용자 기준으로 보호한다.
    if (req.method==='GET' && pathname==='/api/me') return send(res,200,{user:safeUser(u)}); // 현재 사용자 정보를 반환한다.
    if (req.method==='PUT' && pathname==='/api/me') { const b=await body(req); if(b.name)u.name=b.name; if(b.settings)u.settings={...u.settings,...b.settings}; if(b.password){const h=hash(b.password);u.passwordHash=h.digest;u.salt=h.salt;} save(); return send(res,200,{user:safeUser(u)}); } // 이름·설정·비밀번호를 부분 수정한다.
    if (req.method==='GET' && pathname==='/api/files') return send(res,200,{files:db.files.filter(f=>f.ownerId===u.id).sort((a,b)=>b.createdAt.localeCompare(a.createdAt))}); // 본인 소유 파일만 최신순으로 반환한다.
    if (req.method==='POST' && pathname==='/api/files') { const b=await body(req); if(!b.name||!b.content) return send(res,400,{error:'파일을 선택하세요.'}); const fid=id('file'), name=publicFileName(b.name), ext=path.extname(name); fs.writeFileSync(path.join(FILES,fid+ext),Buffer.from(b.content.split(',').pop(),'base64')); const f={id:fid,ownerId:u.id,name,size:Number(b.size||0),mime:b.mime||'application/octet-stream',diskName:fid+ext,createdAt:now()}; db.files.push(f); save(); return send(res,201,{file:f}); } // 파일 내용을 디코딩해 저장하고 메타데이터를 DB에 기록한다.
    if (req.method==='DELETE' && pathname.startsWith('/api/files/')) { const fid=pathname.split('/').pop(), i=db.files.findIndex(f=>f.id===fid&&f.ownerId===u.id); if(i<0)return send(res,404,{error:'파일을 찾을 수 없습니다.'}); const f=db.files[i]; try{fs.unlinkSync(path.join(FILES,f.diskName));}catch{} db.files.splice(i,1); save(); return send(res,200,{ok:true}); } // 본인 파일의 실제 파일과 메타데이터를 함께 삭제한다.
    if (req.method==='GET' && pathname.startsWith('/api/files/')) { const fid=pathname.split('/').pop(), f=db.files.find(x=>x.id===fid&&x.ownerId===u.id); if(!f)return send(res,404,{error:'파일을 찾을 수 없습니다.'}); res.writeHead(200,{'Content-Type':f.mime,'Content-Disposition':`attachment; filename*=UTF-8''${encodeURIComponent(f.name)}`}); return fs.createReadStream(path.join(FILES,f.diskName)).pipe(res); } // 본인 파일만 다운로드 스트림으로 반환한다.
    if (req.method==='GET' && pathname==='/api/mails') { const folder=new URL(req.url,'http://localhost').searchParams.get('folder')||'inbox'; const mails=db.mails.filter(m=>m.to.includes(u.email)&&m.folder===folder || m.from===u.email&&m.folder===folder).sort((a,b)=>b.createdAt.localeCompare(a.createdAt)); return send(res,200,{mails}); } // 받은·보낸 메일 중 현재 폴더에 맞는 메일을 최신순으로 반환한다.
    if (req.method==='POST' && pathname==='/api/mails') { const b=await body(req); const folder=b.action==='draft'?'drafts':'sent'; const m={id:id('mail'),from:u.email,to:Array.isArray(b.to)?b.to:String(b.to||'').split(',').map(x=>x.trim()).filter(Boolean),subject:b.subject||'(제목 없음)',body:b.body||'',folder,read:false,createdAt:now()}; db.mails.push(m); if(folder==='sent') m.to.forEach(email=>{if(!db.users.some(x=>x.email===email)){} }); save(); return send(res,201,{mail:m}); } // 메일 또는 임시 메일을 만들고 DB에 저장한다.
    if (req.method==='PUT' && pathname.startsWith('/api/mails/')) { const m=db.mails.find(x=>x.id===pathname.split('/').pop()&&(x.to.includes(u.email)||x.from===u.email)); if(!m)return send(res,404,{error:'메일을 찾을 수 없습니다.'}); const b=await body(req); if(b.read!==undefined)m.read=b.read; save(); return send(res,200,{mail:m}); } // 본인이 관련된 메일의 읽음 상태를 변경한다.
    if (req.method==='GET' && pathname==='/api/admin/users') { const a=auth(req,res,true); if(!a)return; return send(res,200,{users:db.users.map(safeUser)}); } // 관리자만 전체 사용자 목록을 조회할 수 있게 한다.
    if (req.method==='PUT' && pathname.startsWith('/api/admin/users/')) { const a=auth(req,res,true); if(!a)return; const target=db.users.find(x=>x.id===pathname.split('/').pop()); if(!target)return send(res,404,{error:'회원을 찾을 수 없습니다.'}); const b=await body(req); if(b.grade)target.grade=b.grade; if(b.blocked!==undefined)target.blocked=Boolean(b.blocked); save(); return send(res,200,{user:safeUser(target)}); } // 관리자가 회원 등급과 차단 상태를 변경한다.
    if (req.method==='POST' && pathname==='/api/admin/announcement') { const a=auth(req,res,true); if(!a)return; const b=await body(req); const targets=db.users.filter(x=>x.role==='client').map(x=>x.email); const m={id:id('mail'),from:a.email,to:targets,subject:b.subject||'Jewel Cloud 공지',body:b.body||'',folder:'inbox',read:false,createdAt:now()}; db.mails.push(m); save(); return send(res,201,{mail:m,recipients:targets.length}); } // 관리자의 공지 메일을 모든 일반 사용자에게 저장한다.
    return send(res,404,{error:'API 경로를 찾을 수 없습니다.'}); // 일치하는 API가 없으면 404를 반환한다.
  } catch(e) { console.error(e); return send(res,500,{error:'서버 오류가 발생했습니다.'}); } // 예외를 로그에 남기고 일반 서버 오류로 응답한다.
}
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json'}; // 정적 파일 확장자별 응답 MIME 타입을 정의한다.
const server=http.createServer((req,res)=>{const p=new URL(req.url,'http://localhost').pathname; if(p.startsWith('/api/'))return api(req,res,p); const file=p==='/'?'/index.html':p; const fp=path.join(ROOT,'public',path.normalize(file)); if(!fp.startsWith(path.join(ROOT,'public')))return send(res,403,{error:'forbidden'}); fs.readFile(fp,(e,d)=>e?send(res,404,'Not found','text/plain'):send(res,200,d,mime[path.extname(fp)]||'text/plain; charset=utf-8'));}); // API와 public 정적 파일 요청을 분기하는 HTTP 서버를 만든다.
server.listen(process.env.PORT||3000,()=>console.log(`Jewel Cloud listening on http://localhost:${process.env.PORT||3000}`)); // 지정 포트에서 서버를 시작하고 접속 주소를 출력한다.
