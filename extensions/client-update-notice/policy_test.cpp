// Standalone, dependency-free maintainer test for the shared advisory policy.
#include "client_update_notice.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
int main() {
 using namespace drx_update;
 for(const char* bad:{"","0","-1","+779","779bad","779.0","779;quit","1000001","999999999999999999999"}) assert(!version(bad));
 assert(version("833")==833 && version(" \t833\n")==833);
 assert(!answer("ca client_version_local_extra 779"));
 assert(!answer("ca password secret"));
 Slot slot;
 assert(!slot.receive("ca client_version_local 779",19,100));
 assert(slot.begin(19,100));assert(!slot.begin(19,101));
 assert(slot.receive("ca client_version_local 779",19,102));
 assert(slot.shouldNotify(19,833));assert(!slot.shouldNotify(20,833));
 assert(!slot.shouldNotify(19,779));assert(!slot.shouldNotify(19,778));
 slot.notified=true;assert(!slot.shouldNotify(19,834));
 slot.reset(true);assert(!slot.begin(19,103));
 slot.reset(false);assert(slot.begin(19,104));
 assert(slot.receive("ca client_version_local -1",19,105));assert(!slot.shouldNotify(19,833));
 slot.reset(false);assert(slot.begin(19,200));
 assert(slot.receive("ca client_version_local 779",19,200+replyTimeoutMs+1));
 assert(!slot.shouldNotify(19,833));
 slot.reset(false);assert(slot.begin(19,400));slot.reset(true);
 assert(slot.receive("ca client_version_local 779",19,401));assert(!slot.shouldNotify(19,833));
 std::puts("PASS update-notice policy (no server/client/network runtime)");
}
