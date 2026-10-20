// Actual public adapter, mocked libcurl transport, retained old client responder.
#include <atomic>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <map>
#include <string>
#include <thread>
#include <vector>
#include <curl/curl.h>
const int MAX_CLIENTS=64,AUTH_AUTHED=4;
struct cvar_t {const char* name;const char* string;int integer;};
struct Client {struct {unsigned uid=0;} info;bool active=false,isVirtual=false;int auth_state=0;};
struct {Client clients[MAX_CLIENTS];} sl;
struct Sent {int recipient;std::string text;};
std::vector<Sent> queries,notices;
std::thread::id mainThread;
struct {
 void Cvar_Register(cvar_t* c){c->integer=std::atoi(c->string);}
 void Server_SendMessage(int sender,int slot,const char* text){assert(sender==-1&&std::this_thread::get_id()==mainThread);queries.push_back({slot,text});}
} cores;
void SV_ClientEcho(int slot,const char* text){assert(std::this_thread::get_id()==mainThread);notices.push_back({slot,text});}
std::atomic<int> calls{0};std::atomic<bool> gate{false};
std::string body="833";long httpStatus=200;CURLcode curlResult=CURLE_OK;
struct CurlFixture {std::map<CURLoption,long> options;curl_write_callback write=nullptr;void* data=nullptr;std::string url;};
CurlFixture transport;
CURLcode curl_global_init(long flags){assert(std::this_thread::get_id()==mainThread&&flags==CURL_GLOBAL_DEFAULT);return CURLE_OK;}
#undef curl_easy_setopt
CURL* curl_easy_init(){transport=CurlFixture{};return reinterpret_cast<CURL*>(&transport);}
CURLcode curl_easy_setopt(CURL*,CURLoption key,...) {
 va_list args;va_start(args,key);
 if(key==CURLOPT_URL)transport.url=va_arg(args,const char*);
 else if(key==CURLOPT_WRITEFUNCTION)transport.write=va_arg(args,curl_write_callback);
 else if(key==CURLOPT_WRITEDATA)transport.data=va_arg(args,void*);
 else transport.options[key]=va_arg(args,long);
 va_end(args);return CURLE_OK;
}
CURLcode curl_easy_perform(CURL*) {
 ++calls;while(gate.load())std::this_thread::yield();
 assert(transport.url=="https://api.savagedrx.com/updater/v2/client/version");
 assert(transport.options.size()==8);
 assert(transport.options[CURLOPT_HTTPGET]==1&&transport.options[CURLOPT_NOSIGNAL]==1);
 assert(transport.options[CURLOPT_CONNECTTIMEOUT_MS]==1000&&transport.options[CURLOPT_TIMEOUT_MS]==2000);
 assert(transport.options[CURLOPT_FOLLOWLOCATION]==0&&transport.options[CURLOPT_SSL_VERIFYPEER]==1);
 assert(transport.options[CURLOPT_SSL_VERIFYHOST]==2&&transport.options[CURLOPT_PROTOCOLS]==CURLPROTO_HTTPS);
 // No credentials, arbitrary headers, redirects, POST or engine calls.
 const size_t half=body.size()/2;
 if(transport.write(&body[0],1,half,transport.data)!=half)return CURLE_WRITE_ERROR;
 if(transport.write(&body[0]+half,1,body.size()-half,transport.data)!=body.size()-half)return CURLE_WRITE_ERROR;
 return curlResult;
}
CURLcode curl_easy_getinfo(CURL*,CURLINFO key,...) {
 assert(key==CURLINFO_RESPONSE_CODE);va_list args;va_start(args,key);
 *va_arg(args,long*)=httpStatus;va_end(args);return CURLE_OK;
}
void curl_easy_cleanup(CURL*){}
#define DRX_CLIENT_UPDATE_NOTICE_IMPLEMENTATION
#include "client_update_notice_game.h"
static char fmtBuffer[4096];
const char* fmt(const char* format,...) {va_list args;va_start(args,format);vsnprintf(fmtBuffer,sizeof fmtBuffer,format,args);va_end(args);return fmtBuffer;}
int CheckMinimapPanel(const char*,bool){return 0;}
std::string clientValue="779";int senderSlot=0;
struct {
 const char* Cvar_GetString(const char* name){assert(!strcmp(name,"client_version_local"));return clientValue.c_str();}
 void Client_SendMessageToServer(const char* text){assert(SV_ClientUpdateMessage(senderSlot,text));}
} corec;
#include "old_client_answer.cpp"
int checks=0;
void check(bool value){++checks;assert(value);}
void waitFor(const std::function<bool()>& condition,bool pump=true) {
 const auto until=std::chrono::steady_clock::now()+std::chrono::seconds(5);
 while(!condition()){assert(std::chrono::steady_clock::now()<until);if(pump)SV_ClientUpdateFrame();std::this_thread::yield();}
}
void attach(int slot,unsigned uid,int auth=AUTH_AUTHED) {
 SV_ClientUpdateReset(slot,false);sl.clients[slot]=Client{};
 sl.clients[slot].active=true;sl.clients[slot].info.uid=uid;sl.clients[slot].auth_state=auth;
 SV_ClientUpdateAccepted(slot);
}
void answer(int slot,const std::string& value) {
 senderSlot=slot;clientValue=value;char key[]="client_version_local";CL_CvarAnswer(key);
}
int main() {
 mainThread=std::this_thread::get_id();
 // Directly test the actual bounded callback/transport, including invalid bodies.
 for(const std::string& value:{std::string("833"),std::string(" \t833\r\n")}){body=value;check(UpdateFetch()==833);}
 for(const std::string& value:{std::string(""),std::string("833junk"),std::string(40,'8'),std::string("833\0bad",7)}){body=value;check(!UpdateFetch());}
 body="833";httpStatus=503;check(!UpdateFetch());httpStatus=200;
 curlResult=CURLE_OPERATION_TIMEDOUT;check(!UpdateFetch());curlResult=CURLE_OK;
 UpdateResponse bounded;
 char one='x';check(!UpdateWrite(&one,2,static_cast<size_t>(-1),&bounded));check(!bounded.used);
 calls=0;gate=true;SV_ClientUpdateInit();
 attach(0,19);check(queries.size()==1&&queries[0].recipient==0&&queries[0].text=="sca client_version_local");
 waitFor([]{return calls==1;});answer(0,"779");check(notices.empty());
 // A blocked lookup does not block another accepted connection or game frame.
 attach(1,442);answer(1,"833");check(queries.size()==2&&notices.empty());
 gate=false;waitFor([]{return notices.size()==1;});check(notices[0].recipient==0);
 check(notices[0].text.find("779")!=std::string::npos&&notices[0].text.find("833")!=std::string::npos);
 for(int i=0;i<1000;++i)SV_ClientUpdateFrame();
 answer(0,"779");SV_ClientUpdateAccepted(0);check(calls==1&&queries.size()==2&&notices.size()==1);
 check(!SV_ClientUpdateMessage(0,"ca host_maxfps 1000"));
 for(const char* value:{"832","833","834","999999","","-1","0","bad","779;quit"}) {
  const auto before=notices.size();attach(2,1002);answer(2,value);
  check(notices.size()==before+(!strcmp(value,"832")?1:0));
 }
 auto before=notices.size();auto q=queries.size();
 SV_ClientUpdateReset(0,true);SV_ClientUpdateAccepted(0);check(queries.size()==q&&notices.size()==before);
 attach(0,19);answer(0,"779");check(notices.size()==before+1);
 attach(3,1003);sl.clients[3].info.uid=1004;answer(3,"779");check(notices.size()==before+1);
 attach(4,1004);sl.clients[4].isVirtual=true;check(!SV_ClientUpdateMessage(4,"ca client_version_local 779"));
 q=queries.size();attach(5,1005,0);check(queries.size()==q);
 sv_clientUpdateNotice.integer=0;attach(6,1006);check(queries.size()==q);sv_clientUpdateNotice.integer=1;
 attach(7,1007);sv_clientUpdateNotice.integer=0;answer(7,"779");check(notices.size()==before+1);sv_clientUpdateNotice.integer=1;
 httpStatus=503;updateLatestAt=0;updateLatest=0;updateAttemptAt=0;
 attach(8,1008);answer(8,"779");waitFor([]{return updatePublished.load();},false);SV_ClientUpdateFrame();check(notices.size()==before+1);
 attach(9,1009);answer(9,"779");check(calls==2&&notices.size()==before+1);
 sv_clientUpdateLatest.integer=833;attach(10,1010);answer(10,"779");check(notices.size()==before+2&&notices.back().recipient==10);
 sv_clientUpdateLatest.integer=0;httpStatus=200;body="833bad";updateAttemptAt=0;
 attach(11,1011);answer(11,"779");waitFor([]{return updatePublished.load();},false);SV_ClientUpdateFrame();check(!updateLatest&&calls==3);
 updateLatest=833;updateLatestAt=UpdateNow()-900001;attach(12,1012);answer(12,"779");check(notices.size()==before+2);
 SV_ClientUpdateShutdown();SV_ClientUpdateShutdown();check(!updateStarted&&!updateWorker.joinable());
 std::printf("PASS %d checks; actual public adapter, retained old-client responder; libcurl mocked\n",checks);
}
