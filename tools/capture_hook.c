#define _GNU_SOURCE
#include <dlfcn.h>
#include <pthread.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
typedef struct {uint32_t codec;uint32_t compression;_Bool hud;_Bool input;} Options;
static void touch(const char* p){FILE*f=fopen(p,"w");if(f){fputs("ok",f);fclose(f);}}
static void* worker(void*x){
 const char* base=getenv("TOPGUN_CAPTURE_SYNC");if(!base)return NULL;
 char go[1024],ack[1024],done[1024],end[1024],avi[1024],wav[1024];
 snprintf(go,sizeof(go),"%s.go",base);snprintf(ack,sizeof(ack),"%s.ack",base);snprintf(done,sizeof(done),"%s.done",base);snprintf(end,sizeof(end),"%s.end",base);snprintf(avi,sizeof(avi),"%s.avi",base);snprintf(wav,sizeof(wav),"%s.wav",base);
 for(int i=0;i<60000;i++){if(!access(go,F_OK))break;usleep(10000);}
 void*c=dlopen(getenv("MESEN_CORE_PATH"),RTLD_LAZY|RTLD_NOLOAD);if(!c)return NULL;
 void(*start)(const char*,Options)=dlsym(c,"AviRecord");void(*stop)(void)=dlsym(c,"AviStop");void(*wave)(const char*)=dlsym(c,"WaveRecord");void(*stopwave)(void)=dlsym(c,"WaveStop");
 if(!start||!stop||!wave||!stopwave)return NULL;
 Options opts={2,1,0,0};start(avi,opts);wave(wav);touch(ack);
 for(int i=0;i<60000;i++){if(!access(done,F_OK))break;usleep(10000);}
 stop();stopwave();touch(end);return NULL;
}
__attribute__((constructor)) static void init(void){pthread_t t;pthread_create(&t,NULL,worker,NULL);pthread_detach(t);}
