#define _GNU_SOURCE
#include <dlfcn.h>
#include <pthread.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/stat.h>
typedef struct {uint32_t codec;uint32_t compression;_Bool hud;_Bool input;} Options;
static void touch(const char* p){FILE*f=fopen(p,"w");if(f){fputs("ok",f);fclose(f);}}
/* AviStop releases a shared recorder; its last rendering reference can finish
   asynchronously. Let its destructor finalize the RIFF header before Lua exits. */
static void wait_avi_header(const char* p){
 for(int i=0;i<200;i++){
  char h[4]={0};FILE*f=fopen(p,"rb");
  if(f){size_t n=fread(h,1,4,f);fclose(f);if(n==4&&!memcmp(h,"RIFF",4))return;}
  usleep(10000);
 }
 fprintf(stderr,"AVI finalization timeout: %s\n",p);
}
static void wait_wave_header(const char* p){
 for(int i=0;i<200;i++){
  unsigned char h[12]={0};struct stat st;FILE*f=fopen(p,"rb");
  if(f){size_t n=fread(h,1,12,f);fclose(f);
   uint32_t size=(uint32_t)h[4]|((uint32_t)h[5]<<8)|((uint32_t)h[6]<<16)|((uint32_t)h[7]<<24);
   if(n==12&&!memcmp(h,"RIFF",4)&&!memcmp(h+8,"WAVE",4)&&size>36&&
      !stat(p,&st)&&(uint64_t)size+8==(uint64_t)st.st_size)return;
  }
  usleep(10000);
 }
 fprintf(stderr,"WAV finalization timeout: %s\n",p);
}
static void* worker(void*x){
 const char* base=getenv("TOPGUN_CAPTURE_SYNC");if(!base)return NULL;
 char go[1024],ack[1024],done[1024],end[1024],avi[1024],wav[1024];
 snprintf(go,sizeof(go),"%s.go",base);snprintf(ack,sizeof(ack),"%s.ack",base);snprintf(done,sizeof(done),"%s.done",base);snprintf(end,sizeof(end),"%s.end",base);snprintf(avi,sizeof(avi),"%s.avi",base);snprintf(wav,sizeof(wav),"%s.wav",base);
 for(int i=0;i<60000;i++){if(!access(go,F_OK))break;usleep(10000);}
 void*c=dlopen(getenv("MESEN_CORE_PATH"),RTLD_LAZY|RTLD_NOLOAD);if(!c)return NULL;
 void(*start)(const char*,Options)=dlsym(c,"AviRecord");void(*stop)(void)=dlsym(c,"AviStop");void(*wave)(const char*)=dlsym(c,"WaveRecord");void(*stopwave)(void)=dlsym(c,"WaveStop");
 if(!start||!stop||!wave||!stopwave)return NULL;
 /* A repeated run must not mistake the previous AVI's RIFF header for the
    new recorder's completion. These are the outputs this run replaces. */
 unlink(avi);unlink(wav);
 Options opts={2,1,0,0};start(avi,opts);wave(wav);touch(ack);
 for(int i=0;i<60000;i++){if(!access(done,F_OK))break;usleep(10000);}
 stop();stopwave();wait_avi_header(avi);wait_wave_header(wav);touch(end);return NULL;
}
__attribute__((constructor)) static void init(void){pthread_t t;pthread_create(&t,NULL,worker,NULL);pthread_detach(t);}
