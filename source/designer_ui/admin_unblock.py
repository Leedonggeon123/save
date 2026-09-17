<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>UnblockMainWindow</class>
 <widget class="QMainWindow" name="UnblockMainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>1280</width>
    <height>800</height>
   </rect>
  </property>
  <property name="minimumSize">
   <size>
    <width>1280</width>
    <height>800</height>
   </size>
  </property>
  <property name="maximumSize">
   <size>
    <width>1280</width>
    <height>800</height>
   </size>
  </property>
  <property name="windowTitle">
   <string>Jewel</string>
  </property>
  <property name="styleSheet">
   <string notr="true">QMainWindow { background: #ffffff; } QFrame#titleBar { background: #a8cadf; } QFrame#sideBar { background: #e5f4fe; border-right: 1px solid #1d1d1d; } QPushButton { border: none; background: transparent; font: 700 14px &quot;Malgun Gothic&quot;; text-align: left; padding-left: 27px; } QPushButton#unblockButton { color: #0078ff; } QPushButton#logoutButton, QPushButton#actionButton { background: #49adf0; color: #000000; border-radius: 8px; font: 700 14px &quot;Malgun Gothic&quot;; padding: 0px; text-align: center; } QListWidget { border: 1px solid #111111; background: #ffffff; }</string>
  </property>
  <widget class="QWidget" name="centralwidget">
   <widget class="QFrame" name="titleBar">
    <property name="geometry">
     <rect>
      <x>0</x>
      <y>0</y>
      <width>1280</width>
      <height>40</height>
     </rect>
    </property>
    <property name="frameShape">
     <enum>QFrame::NoFrame</enum>
    </property>
    <widget class="QPushButton" name="minimizeButton">
     <property name="geometry">
      <rect>
       <x>1200</x>
       <y>0</y>
       <width>38</width>
       <height>40</height>
      </rect>
     </property>
     <property name="text">
      <string>−</string>
     </property>
     <property name="styleSheet">
      <string notr="true">QPushButton { font: 20px &quot;Arial&quot;; padding: 0; }</string>
     </property>
    </widget>
    <widget class="QPushButton" name="closeButton">
     <property name="geometry">
      <rect>
       <x>1238</x>
       <y>0</y>
       <width>38</width>
       <height>40</height>
      </rect>
     </property>
     <property name="text">
      <string>×</string>
     </property>
     <property name="styleSheet">
      <string notr="true">QPushButton { font: 24px &quot;Arial&quot;; padding: 0; }</string>
     </property>
    </widget>
   </widget>
   <widget class="QFrame" name="sideBar">
    <property name="geometry">
     <rect>
      <x>0</x>
      <y>40</y>
      <width>228</width>
      <height>760</height>
     </rect>
    </property>
    <property name="frameShape">
     <enum>QFrame::StyledPanel</enum>
    </property>
    <widget class="QLabel" name="logoLabel">
     <property name="geometry">
      <rect>
       <x>19</x>
       <y>18</y>
       <width>92</width>
       <height>72</height>
      </rect>
     </property>
     <property name="pixmap">
      <pixmap resource="jewel_resources.qrc">:/jewel/assets/jewel_logo.svg</pixmap>
     </property>
     <property name="scaledContents">
      <bool>true</bool>
     </property>
    </widget>
    <widget class="QLabel" name="brandLabel">
     <property name="geometry">
      <rect>
       <x>123</x>
       <y>34</y>
       <width>78</width>
       <height>40</height>
      </rect>
     </property>
     <property name="text">
      <string>Jewel</string>
     </property>
     <property name="styleSheet">
      <string notr="true">font: 700 26px &quot;Arial&quot;; color: #080808;</string>
     </property>
    </widget>
    <widget class="QPushButton" name="blockButton">
     <property name="geometry">
      <rect>
       <x>0</x>
       <y>105</y>
       <width>220</width>
       <height>48</height>
      </rect>
     </property>
     <property name="text">
      <string>차단</string>
     </property>
    </widget>
    <widget class="QPushButton" name="unblockButton">
     <property name="geometry">
      <rect>
       <x>0</x>
       <y>153</y>
       <width>220</width>
       <height>48</height>
      </rect>
     </property>
     <property name="text">
      <string>차단 풀기</string>
     </property>
    </widget>
    <widget class="QPushButton" name="noticeButton">
     <property name="geometry">
      <rect>
       <x>0</x>
       <y>201</y>
       <width>220</width>
       <height>48</height>
      </rect>
     </property>
     <property name="text">
      <string>공지</string>
     </property>
    </widget>
    <widget class="QPushButton" name="membershipButton">
     <property name="geometry">
      <rect>
       <x>0</x>
       <y>249</y>
       <width>220</width>
       <height>48</height>
      </rect>
     </property>
     <property name="text">
      <string>회원등급</string>
     </property>
    </widget>
   </widget>
   <widget class="QPushButton" name="logoutButton">
    <property name="geometry">
     <rect>
      <x>1110</x>
      <y>53</y>
      <width>160</width>
      <height>44</height>
     </rect>
    </property>
    <property name="text">
      <string>로그아웃</string>
     </property>
   </widget>
   <widget class="QLabel" name="titleLabel">
    <property name="geometry">
     <rect>
      <x>238</x>
      <y>140</y>
      <width>140</width>
      <height>25</height>
     </rect>
    </property>
    <property name="text">
      <string>차단한 아이디 목록</string>
    </property>
    <property name="styleSheet">
     <string notr="true">font: 14px &quot;Malgun Gothic&quot;; color: #000;</string>
    </property>
   </widget>
   <widget class="QListWidget" name="idListWidget">
    <property name="geometry">
     <rect>
      <x>238</x>
      <y>175</y>
      <width>970</width>
      <height>560</height>
     </rect>
    </property>
   </widget>
   <widget class="QPushButton" name="actionButton">
    <property name="geometry">
     <rect>
      <x>559</x>
      <y>748</y>
      <width>128</width>
      <height>36</height>
     </rect>
    </property>
    <property name="text">
      <string>차단 풀기</string>
    </property>
   </widget>
  </widget>
 </widget>
 <resources>
  <include location="jewel_resources.qrc"/>
 </resources>
 <connections/>
</ui>