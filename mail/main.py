"""Jewel Cloud FastAPI server.

The SQLite tables mirror the supplied data definition: USER, File_Metadata,
USER_SETTINGS, MESSAGES, TEMP_MESSAGES and BLACKLIST. HTTP runs over TCP/IP.
"""
from __future__ import annotations  # 타입 힌트를 지연 평가한다.
import hashlib, hmac, secrets, sqlite3  # 비밀번호 해시·보안 비교·토큰·SQLite를 사용한다.
from datetime import datetime, timezone  # UTC 생성 시각을 만든다.
from pathlib import Path  # 파일 경로를 운영체제와 무관하게 조합한다.
from typing import Optional  # 선택적 입력 필드 타입을 표현한다.
from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile  # FastAPI 앱과 요청·응답·파일 기능을 가져온다.
from fastapi.middleware.cors import CORSMiddleware  # 브라우저의 교차 출처 요청을 허용한다.
from fastapi.responses import FileResponse, HTMLResponse  # 파일과 HTML 응답 형식을 제공한다.
from fastapi.staticfiles import StaticFiles  # public 정적 파일을 서비스한다.
from pydantic import BaseModel  # API 입력값을 검증하는 모델의 기반 클래스다.

ROOT = Path(__file__).parent  # main.py가 있는 mail 프로젝트 경로를 기준점으로 잡는다.
DATA = ROOT / "data"  # 데이터 폴더 경로를 계산한다.
UPLOADS = DATA / "files"  # 업로드 파일 폴더 경로를 계산한다.
DB = DATA / "jewel_cloud.sqlite3"  # 웹 서버가 사용할 SQLite DB 경로다.
DATA.mkdir(exist_ok=True); UPLOADS.mkdir(exist_ok=True)  # 필요한 폴더가 없으면 생성한다.
app = FastAPI(title="Jewel Cloud API", version="1.0.0", description="TCP/IP HTTP API for Jewel Cloud")  # FastAPI 애플리케이션을 만든다.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])  # 프런트엔드의 API 호출을 허용한다.
SESSIONS: dict[str, int] = {}  # 메모리에서 세션 토큰과 사용자 ID를 연결한다.

def utc(): return datetime.now(timezone.utc).isoformat()  # 서버 시각을 UTC ISO 문자열로 반환한다.
def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c  # DB를 열고 컬럼명 접근·외래키를 활성화한다.
def password_hash(value: str, salt: Optional[str]=None):
    salt=salt or secrets.token_hex(16); return salt, hashlib.scrypt(value.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=64).hex()  # salt와 scrypt 해시를 생성한다.
def password_ok(value, salt, digest): return hmac.compare_digest(password_hash(value,salt)[1],digest)  # 입력 비밀번호의 해시를 저장값과 안전하게 비교한다.
def user_dict(row):
    if not row:return None  # 조회 결과가 없으면 사용자도 없음을 반환한다.
    d=dict(row); d.pop("password_hash",None); d.pop("password_salt",None)  # 민감한 인증 정보를 응답에서 제거한다.
    d["settings"]={"autoFit":bool(d.pop("auto_fit",1)),"defaultSenderEmail":d.pop("default_sender_email",d["email"]),"prefixMsg":d.pop("prefix_msg","") ,"suffixMsg":d.pop("suffix_msg","") ,"downloadPath":d.pop("download_path","")}  # DB 설정 컬럼을 클라이언트 형식으로 변환한다.
    d["role"]="admin" if d["is_admin"] else "client"; d["blocked"]=bool(d["is_banned"])  # 관리자 역할과 차단 상태를 계산한다.
    return d  # 안전한 사용자 정보를 반환한다.
def init():
    c=db(); c.executescript("""  # 웹 서버에 필요한 관계형 테이블을 생성한다.
    CREATE TABLE IF NOT EXISTS USER (user_id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,password_salt TEXT NOT NULL,name TEXT NOT NULL,grade TEXT NOT NULL DEFAULT '일반',file_limit INTEGER NOT NULL DEFAULT 0,is_admin INTEGER NOT NULL DEFAULT 0,is_banned INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS File_Metadata (file_id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,file_name TEXT NOT NULL,file_size INTEGER NOT NULL,file_path TEXT NOT NULL,mime_type TEXT NOT NULL DEFAULT 'application/octet-stream',created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES USER(user_id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS USER_SETTINGS (setting_id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL UNIQUE,default_sender_email TEXT,prefix_msg TEXT,suffix_msg TEXT,download_path TEXT,auto_fit INTEGER NOT NULL DEFAULT 1,FOREIGN KEY(user_id) REFERENCES USER(user_id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS MESSAGES (msg_id INTEGER PRIMARY KEY AUTOINCREMENT,sender_id INTEGER NOT NULL,receiver_id INTEGER NOT NULL,content TEXT NOT NULL,subject TEXT NOT NULL DEFAULT '(제목 없음)',folder TEXT NOT NULL DEFAULT 'sent',is_read INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,FOREIGN KEY(sender_id) REFERENCES USER(user_id),FOREIGN KEY(receiver_id) REFERENCES USER(user_id));
    CREATE TABLE IF NOT EXISTS TEMP_MESSAGES (temp_msg_id INTEGER PRIMARY KEY AUTOINCREMENT,sender_id INTEGER NOT NULL,receiver_id INTEGER,content TEXT NOT NULL,subject TEXT NOT NULL DEFAULT '(제목 없음)',created_at TEXT NOT NULL,FOREIGN KEY(sender_id) REFERENCES USER(user_id));
    CREATE TABLE IF NOT EXISTS BLACKLIST (blocker_id INTEGER NOT NULL,blocked_id INTEGER NOT NULL,PRIMARY KEY(blocker_id,blocked_id),FOREIGN KEY(blocker_id) REFERENCES USER(user_id),FOREIGN KEY(blocked_id) REFERENCES USER(user_id));
    """)
    if not c.execute("SELECT 1 FROM USER WHERE email=?",("admin@jewel.cloud",)).fetchone():  # 기본 관리자가 없을 때만 초기 계정을 만든다.
        for email,pw,name,admin in [("admin@jewel.cloud","admin1234","Jewel 관리자",1),("user@jewel.cloud","user1234","데모 사용자",0)]:
            salt,digest=password_hash(pw); cur=c.execute("INSERT INTO USER(email,password_hash,password_salt,name,is_admin,created_at) VALUES(?,?,?,?,?,?)",(email,digest,salt,name,admin,utc())); uid=cur.lastrowid; c.execute("INSERT INTO USER_SETTINGS(user_id,default_sender_email) VALUES(?,?)",(uid,email))  # 계정과 사용자별 기본 설정을 함께 저장한다.
    c.commit(); c.close()  # 스키마·초기 데이터를 확정하고 DB 연결을 닫는다.
init()  # 모듈을 불러올 때 DB가 즉시 준비되도록 초기화한다.

class Signup(BaseModel): email: str; password: str; name: str  # 회원가입 요청 필수 필드를 정의한다.
class Login(BaseModel): email: str; password: str  # 로그인 요청 필드를 정의한다.
class Profile(BaseModel): name: Optional[str]=None; password: Optional[str]=None; settings: Optional[dict]=None  # 프로필 수정 필드를 정의한다.
class MailIn(BaseModel): to: str|list[str]; subject: str="(제목 없음)"; body: str=""; action: str="send"  # 메일·임시 저장 입력 형식을 정의한다.
class UserPolicy(BaseModel): grade: Optional[str]=None; blocked: Optional[bool]=None  # 관리자 정책 변경 필드를 정의한다.
class Announcement(BaseModel): subject: str; body: str  # 공지 메일 입력 필드를 정의한다.

def current(request: Request, admin=False):
    uid=SESSIONS.get(request.cookies.get("jewel_session")); c=db(); row=c.execute("SELECT u.*,s.auto_fit,s.default_sender_email,s.prefix_msg,s.suffix_msg,s.download_path FROM USER u LEFT JOIN USER_SETTINGS s ON s.user_id=u.user_id WHERE u.user_id=?",(uid,)).fetchone() if uid else None; c.close()  # 세션 쿠키로 사용자를 찾고 설정을 함께 조회한다.
    if not row or row["is_banned"] or (admin and not row["is_admin"]): raise HTTPException(403,"인증 또는 권한이 필요합니다.")  # 인증·차단·관리자 권한을 검사한다.
    return row  # 인증된 사용자 행을 반환한다.
def public_files(row):
    return {"id":row["file_id"],"ownerId":row["user_id"],"name":row["file_name"],"size":row["file_size"],"mime":row["mime_type"],"createdAt":row["created_at"]}  # 파일 DB 행을 클라이언트 응답 형식으로 변환한다.
def public_mail(m):
    return {"id":m["msg_id"],"from":m["sender_email"],"to":[m["receiver_email"]],"subject":m["subject"],"body":m["content"],"folder":m["folder"],"read":bool(m["is_read"]),"createdAt":m["created_at"]}  # 메일 DB 행을 클라이언트 응답 형식으로 변환한다.

@app.get("/api/health")
def health(): return {"ok":True,"transport":"HTTP over TCP/IP","service":"Jewel Cloud"}  # 서버 상태와 통신 방식을 확인할 수 있게 한다.
@app.post("/api/auth/signup")
def signup(x: Signup):
    salt,digest=password_hash(x.password); c=db()  # 비밀번호를 해시하고 DB 연결을 연다.
    try: cur=c.execute("INSERT INTO USER(email,password_hash,password_salt,name,created_at) VALUES(?,?,?,?,?)",(x.email.lower(),digest,salt,x.name,utc())); uid=cur.lastrowid; c.execute("INSERT INTO USER_SETTINGS(user_id,default_sender_email) VALUES(?,?)",(uid,x.email.lower())); c.commit(); return {"user":{"email":x.email.lower(),"name":x.name}}
    except sqlite3.IntegrityError: raise HTTPException(409,"이미 사용 중인 이메일입니다.")  # 이메일 중복을 HTTP 409로 알린다.
    finally:c.close()  # 성공·실패와 관계없이 연결을 닫는다.
@app.post("/api/auth/login")
def login(x: Login, response: Response):
    c=db(); r=c.execute("SELECT * FROM USER WHERE email=?",(x.email.lower(),)).fetchone(); c.close()  # 이메일로 계정을 조회한다.
    if not r or not password_ok(x.password,r["password_salt"],r["password_hash"]) or r["is_banned"]: raise HTTPException(401,"이메일 또는 비밀번호가 올바르지 않습니다.")  # 비밀번호와 차단 상태를 확인한다.
    token=secrets.token_urlsafe(32); SESSIONS[token]=r["user_id"]; response.set_cookie("jewel_session",token,httponly=True,samesite="lax"); return {"user":user_dict(r)}  # 세션을 메모리에 저장하고 쿠키를 발급한다.
@app.post("/api/auth/logout")
def logout(request: Request, response: Response): SESSIONS.pop(request.cookies.get("jewel_session"),None); response.delete_cookie("jewel_session"); return {"ok":True}  # 세션을 삭제하고 브라우저 쿠키를 만료시킨다.
@app.get("/api/me")
def me(request: Request): return {"user":user_dict(current(request))}  # 현재 로그인 사용자 정보를 반환한다.
@app.put("/api/me")
def update_me(x: Profile, request: Request):
    u=current(request); c=db(); sets=[]; vals=[]  # 인증된 사용자와 수정할 SQL 조각을 준비한다.
    if x.name:sets.append("name=?");vals.append(x.name)
    if x.password:
        salt,digest=password_hash(x.password);sets += ["password_hash=?","password_salt=?"];vals += [digest,salt]
    if sets: vals.append(u["user_id"]);c.execute(f"UPDATE USER SET {','.join(sets)} WHERE user_id=?",vals)
    if x.settings:
        s=x.settings;c.execute("UPDATE USER_SETTINGS SET auto_fit=?,default_sender_email=?,prefix_msg=?,suffix_msg=?,download_path=? WHERE user_id=?",(int(s.get("autoFit",True)),s.get("defaultSenderEmail",u["email"]),s.get("prefixMsg",""),s.get("suffixMsg",""),s.get("downloadPath",""),u["user_id"]))
    c.commit(); c.close(); return me(request)  # 변경을 저장하고 최신 사용자 정보를 반환한다.
@app.get("/api/files")
def list_files(request: Request):
    u=current(request); c=db(); rows=c.execute("SELECT * FROM File_Metadata WHERE user_id=? ORDER BY created_at DESC",(u["user_id"],)).fetchall();c.close();return {"files":[public_files(r) for r in rows]}  # 본인 파일만 최신순으로 조회해 반환한다.
@app.post("/api/files")
async def upload(request: Request, file: UploadFile=File(...)):
    u=current(request); fid=secrets.token_hex(10); suffix=Path(file.filename or "file").suffix; disk=fid+suffix; target=UPLOADS/disk; size=0  # 인증 사용자와 서버 저장 파일명을 준비한다.
    with target.open("wb") as out:
        while chunk:=await file.read(1024*1024):out.write(chunk);size+=len(chunk)
    c=db();cur=c.execute("INSERT INTO File_Metadata(user_id,file_name,file_size,file_path,mime_type,created_at) VALUES(?,?,?,?,?,?)",(u["user_id"],file.filename,size,disk,file.content_type or "application/octet-stream",utc()));c.commit();row=c.execute("SELECT * FROM File_Metadata WHERE file_id=?",(cur.lastrowid,)).fetchone();c.close();return {"file":public_files(row)}  # 파일 메타데이터를 저장하고 생성된 파일 정보를 반환한다.
@app.get("/api/files/{fid}")
def download(fid:int, request: Request):
    u=current(request);c=db();r=c.execute("SELECT * FROM File_Metadata WHERE file_id=? AND user_id=?",(fid,u["user_id"])).fetchone();c.close()  # 본인 소유 파일의 메타데이터를 조회한다.
    if not r or not (UPLOADS/r["file_path"]).exists():raise HTTPException(404,"파일을 찾을 수 없습니다.")  # DB와 실제 파일이 모두 있어야 다운로드를 허용한다.
    return FileResponse(UPLOADS/r["file_path"],media_type=r["mime_type"],filename=r["file_name"])  # 파일 응답으로 다운로드를 시작한다.
@app.delete("/api/files/{fid}")
def delete_file(fid:int, request: Request):
    u=current(request);c=db();r=c.execute("SELECT * FROM File_Metadata WHERE file_id=? AND user_id=?",(fid,u["user_id"])).fetchone()  # 본인 파일인지 확인한다.
    if not r:raise HTTPException(404,"파일을 찾을 수 없습니다.")  # 없는 파일이나 타인 파일을 거부한다.
    try:(UPLOADS/r["file_path"]).unlink()  # 실제 저장 파일을 삭제한다.
    except FileNotFoundError:pass  # 실제 파일이 이미 없으면 메타데이터 정리는 계속한다.
    c.execute("DELETE FROM File_Metadata WHERE file_id=?",(fid,));c.commit();c.close();return {"ok":True}  # DB 메타데이터도 삭제한다.
@app.get("/api/mails")
def mails(folder: str="inbox", request: Request=None):
    u=current(request); c=db(); rows=c.execute("SELECT m.*,s.email sender_email,r.email receiver_email FROM MESSAGES m JOIN USER s ON s.user_id=m.sender_id JOIN USER r ON r.user_id=m.receiver_id WHERE (m.sender_id=? OR m.receiver_id=?) AND m.folder=? ORDER BY m.created_at DESC",(u["user_id"],u["user_id"],folder)).fetchall();c.close();return {"mails":[public_mail(r) for r in rows]}  # 현재 사용자와 관련된 폴더 메일을 최신순으로 반환한다.
@app.post("/api/mails")
def send_mail(x: MailIn, request: Request):
    u=current(request); recipients=x.to if isinstance(x.to,list) else [v.strip() for v in x.to.split(",") if v.strip()];c=db()  # 인증 사용자와 수신자 목록을 준비한다.
    if x.action=="draft": c.execute("INSERT INTO TEMP_MESSAGES(sender_id,content,subject,created_at) VALUES(?,?,?,?)",(u["user_id"],x.body,x.subject,utc()));c.commit();c.close();return {"ok":True,"folder":"drafts"}  # 임시 메일은 TEMP_MESSAGES에 저장한다.
    sent=[]  # 실제 존재하는 수신자 목록을 기록한다.
    for email in recipients:
        r=c.execute("SELECT user_id FROM USER WHERE email=?",(email.lower(),)).fetchone()  # 수신자 계정을 조회한다.
        if r:
            c.execute("INSERT INTO MESSAGES(sender_id,receiver_id,content,subject,folder,created_at) VALUES(?,?,?,?,?,?)",(u["user_id"],r["user_id"],x.body,x.subject,"sent",utc()))  # 발신자 메일함용 레코드를 만든다.
            c.execute("INSERT INTO MESSAGES(sender_id,receiver_id,content,subject,folder,created_at) VALUES(?,?,?,?,?,?)",(u["user_id"],r["user_id"],x.body,x.subject,"inbox",utc()));sent.append(email)  # 수신자 메일함용 레코드를 만들고 성공 목록에 추가한다.
    c.commit();c.close();return {"ok":True,"recipients":sent}  # 전송 결과를 저장하고 수신자 목록을 반환한다.
@app.put("/api/mails/{mid}")
def read_mail(mid:int,x:dict,request:Request):
    u=current(request);c=db();c.execute("UPDATE MESSAGES SET is_read=? WHERE msg_id=? AND receiver_id=?",(int(x.get("read",True)),mid,u["user_id"]));c.commit();c.close();return {"ok":True}  # 수신자 본인의 메일만 읽음 상태로 변경한다.
@app.get("/api/admin/users")
def admin_users(request:Request):
    current(request,True);c=db();rows=c.execute("SELECT u.*,s.auto_fit,s.default_sender_email,s.prefix_msg,s.suffix_msg,s.download_path FROM USER u LEFT JOIN USER_SETTINGS s ON s.user_id=u.user_id ORDER BY u.user_id").fetchall();c.close();return {"users":[user_dict(r) for r in rows]}  # 관리자에게 전체 회원과 설정 정보를 반환한다.
@app.put("/api/admin/users/{uid}")
def policy(uid:int,x:UserPolicy,request:Request):
    current(request,True);c=db();c.execute("UPDATE USER SET grade=COALESCE(?,grade),is_banned=COALESCE(?,is_banned) WHERE user_id=?",(x.grade,int(x.blocked) if x.blocked is not None else None,uid));c.commit();c.close();return {"ok":True}  # 관리자만 회원 등급과 차단 상태를 변경한다.
@app.post("/api/admin/announcement")
def announcement(x:Announcement,request:Request):
    u=current(request,True);c=db();targets=c.execute("SELECT user_id,email FROM USER WHERE is_admin=0 AND is_banned=0").fetchall()  # 관리자가 공지를 받을 활성 일반 사용자를 조회한다.
    for r in targets:c.execute("INSERT INTO MESSAGES(sender_id,receiver_id,content,subject,folder,created_at) VALUES(?,?,?,?,?,?)",(u["user_id"],r["user_id"],x.body,x.subject,"inbox",utc()))  # 각 대상의 받은 메일함에 공지를 저장한다.
    c.commit();c.close();return {"ok":True,"recipients":len(targets)}  # 공지 저장을 확정하고 수신자 수를 반환한다.
@app.get("/api/admin/blacklist")
def blacklist(request:Request):
    u=current(request);c=db();rows=c.execute("SELECT b.blocked_id,us.email,us.name FROM BLACKLIST b JOIN USER us ON us.user_id=b.blocked_id WHERE b.blocker_id=?",(u["user_id"],)).fetchall();c.close();return {"blocked":[dict(r) for r in rows]}  # 현재 사용자가 등록한 블랙리스트를 반환한다.
@app.get("/api/blacklist")
def client_blacklist(request:Request): return blacklist(request)  # 클라이언트용 경로를 공통 블랙리스트 조회 함수에 연결한다.
@app.post("/api/blacklist")
def client_add_blacklist(payload:dict,request:Request):
    u=current(request); email=str(payload.get("email","")).lower(); c=db(); target=c.execute("SELECT user_id FROM USER WHERE email=?",(email,)).fetchone()  # 인증 사용자와 차단 대상 계정을 찾는다.
    if not target: c.close(); raise HTTPException(404,"해당 이메일의 사용자를 찾을 수 없습니다.")  # 존재하지 않는 사용자는 차단할 수 없다.
    if target["user_id"]==u["user_id"]: c.close(); raise HTTPException(400,"본인은 차단할 수 없습니다.")  # 자기 자신 차단을 막는다.
    c.execute("INSERT OR IGNORE INTO BLACKLIST(blocker_id,blocked_id) VALUES(?,?)",(u["user_id"],target["user_id"])); c.commit(); c.close(); return {"ok":True}  # 차단 관계를 중복 없이 저장한다.
@app.delete("/api/blacklist/{uid}")
def client_remove_blacklist(uid:int,request:Request): return remove_blacklist(uid,request)  # 클라이언트용 삭제 경로를 공통 함수에 연결한다.
@app.post("/api/admin/blacklist/{uid}")
def add_blacklist(uid:int,request:Request):
    u=current(request);c=db();c.execute("INSERT OR IGNORE INTO BLACKLIST(blocker_id,blocked_id) VALUES(?,?)",(u["user_id"],uid));c.commit();c.close();return {"ok":True}  # 관리자·클라이언트 공통 차단 관계 저장을 처리한다.
@app.delete("/api/admin/blacklist/{uid}")
def remove_blacklist(uid:int,request:Request):
    u=current(request);c=db();c.execute("DELETE FROM BLACKLIST WHERE blocker_id=? AND blocked_id=?",(u["user_id"],uid));c.commit();c.close();return {"ok":True}  # 현재 사용자가 만든 차단 관계만 삭제한다.

app.mount("/", StaticFiles(directory=ROOT/"public", html=True), name="client")  # 나머지 경로에서 public 웹 클라이언트를 제공한다.
