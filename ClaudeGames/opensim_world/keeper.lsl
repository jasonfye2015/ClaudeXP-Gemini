// The Hollow Keeper: a small stone in the Furry Hollow that brings the residents to life.
// It asks the bridge (the computer that launched the world) what to do every few seconds, creates and moves the
// residents' NPCs, says their lines, and passes on what it hears in local chat.
string BRIDGE = "http://127.0.0.1:9180";
list npcs;                       // [first name, key, first name, key, ...]

key npc_named(string first) {
    integer i = llListFindList(npcs, [first]);
    if (i < 0) return NULL_KEY;
    return llList2Key(npcs, i + 1);
}

// what the NPCs wear: the user's own avatar, saved once as a notecard the first time they're in the region
string appearance() {
    if (llGetInventoryType("Appearance") == INVENTORY_NOTECARD) return "Appearance";
    if (llGetAgentSize(llGetOwner()) != ZERO_VECTOR) {
        osAgentSaveAppearance(llGetOwner(), "Appearance");
        if (llGetInventoryType("Appearance") == INVENTORY_NOTECARD) return "Appearance";
    }
    return "";
}

post(string path, string body) {
    llHTTPRequest(BRIDGE + path, [HTTP_METHOD, "POST", HTTP_MIMETYPE, "text/plain;charset=utf-8",
                                  HTTP_BODY_MAXLENGTH, 16384], body);
}

do_line(string line) {
    list f = llParseStringKeepNulls(line, ["|"], []);
    string cmd = llList2String(f, 0);
    if (cmd == "spawn") {                           // spawn|First|Last|x|y|z
        string first = llList2String(f, 1);
        if (npc_named(first) != NULL_KEY) return;
        string look = appearance();
        if (look == "") return;                     // nobody to copy yet: the bridge asks again later
        vector at = <(float)llList2String(f, 3), (float)llList2String(f, 4), (float)llList2String(f, 5)>;
        key k = osNpcCreate(first, llList2String(f, 2), at, look, OS_NPC_SENSE_AS_AGENT);
        if (k != NULL_KEY) {
            npcs += [first, k];
            post("/spawned", first + "|" + (string)k);
        }
    } else if (cmd == "say") {                      // say|First|text
        key k = npc_named(llList2String(f, 1));
        if (k != NULL_KEY) osNpcSay(k, llDumpList2String(llList2List(f, 2, -1), "|"));
    } else if (cmd == "move") {                     // move|First|x|y|z
        key k = npc_named(llList2String(f, 1));
        if (k != NULL_KEY) osNpcMoveToTarget(k, <(float)llList2String(f, 2), (float)llList2String(f, 3),
                                                   (float)llList2String(f, 4)>, OS_NPC_NO_FLY);
    } else if (cmd == "face") {                     // face|First|x|y|z  (turn towards a point)
        key k = npc_named(llList2String(f, 1));
        if (k != NULL_KEY) {
            vector me = osNpcGetPos(k);
            vector to = <(float)llList2String(f, 2), (float)llList2String(f, 3), me.z>;
            osNpcSetRot(k, llRotBetween(<1, 0, 0>, llVecNorm(to - me)));
        }
    } else if (cmd == "remove") {                   // remove|First
        string first = llList2String(f, 1);
        key k = npc_named(first);
        if (k != NULL_KEY) {
            osNpcRemove(k);
            integer i = llListFindList(npcs, [first]);
            npcs = llDeleteSubList(npcs, i, i + 1);
        }
    }
}

default {
    state_entry() {
        llSetText("Hollow Keeper", <0.9, 0.95, 1.0>, 0.5);
        llListen(0, "", NULL_KEY, "");
        llSetTimerEvent(3.0);
    }

    on_rez(integer p) { llResetScript(); }

    listen(integer channel, string name, key id, string message) {
        if (osIsNpc(id)) return;                    // the residents' own lines
        vector at = llList2Vector(llGetObjectDetails(id, [OBJECT_POS]), 0);
        post("/heard", name + "|" + (string)at.x + "|" + (string)at.y + "|" + (string)at.z + "|" + message);
    }

    timer() {
        key owner = llGetOwner();
        string here = "0";
        vector at = ZERO_VECTOR;
        if (llGetAgentSize(owner) != ZERO_VECTOR) {
            here = "1";
            at = llList2Vector(llGetObjectDetails(owner, [OBJECT_POS]), 0);
        }
        llHTTPRequest(BRIDGE + "/poll?here=" + here + "&x=" + (string)at.x + "&y=" + (string)at.y + "&z=" +
                      (string)at.z, [HTTP_METHOD, "GET", HTTP_BODY_MAXLENGTH, 16384], "");
    }

    http_response(key request, integer status, list meta, string body) {
        if (status != 200 || body == "") return;
        list lines = llParseString2List(body, ["\n"], []);
        integer i;
        integer n = llGetListLength(lines);
        for (i = 0; i < n; ++i) do_line(llList2String(lines, i));
    }
}
