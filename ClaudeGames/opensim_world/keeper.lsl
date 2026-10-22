// The Hollow Keeper: a small stone in the Furry Hollow that brings the residents to life.
// There's one in each region. It asks the bridge (the computer that launched the world) what to do every few seconds, creates and moves the
// residents' NPCs, says their lines, and passes on what it hears in local chat. When the owner sits on something
// (a poseball set, a sofa) it says what; a resident invited to join takes the free seat in it, and residents can
// dance to the animations in its contents.
string BRIDGE = "http://127.0.0.1:9180";
list npcs;                       // [first name, key, first name, key, ...]
list dancing;                    // [first name, animation, ...]: who's dancing, to what

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

stop_dance(string first, key k) {
    integer i = llListFindList(dancing, [first]);
    if (i < 0) return;
    if (k != NULL_KEY) osNpcStopAnimation(k, llList2String(dancing, i + 1));
    dancing = llDeleteSubList(dancing, i, i + 1);
}

do_line(string line) {
    list f = llParseStringKeepNulls(line, ["|"], []);
    string cmd = llList2String(f, 0);
    if (cmd == "spawn") {                           // spawn|First|Last|x|y|z[|look]
        string first = llList2String(f, 1);
        key have = npc_named(first);
        if (have != NULL_KEY) {                     // already here: the bridge missed hearing so (a dropped request)
            post("/spawned", llGetRegionName() + "|" + first + "|" + (string)have);
            return;
        }
        string look = llList2String(f, 6);          // the resident's own avatar (a saved look's notecard asset)
        if (look == "") look = appearance();
        if (look == "") return;                     // nobody to copy yet: the bridge asks again later
        vector at = <(float)llList2String(f, 3), (float)llList2String(f, 4), (float)llList2String(f, 5)>;
        key k = osNpcCreate(first, llList2String(f, 2), at, look, OS_NPC_SENSE_AS_AGENT);
        if (k != NULL_KEY) {
            npcs += [first, k];
            post("/spawned", llGetRegionName() + "|" + first + "|" + (string)k);
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
    } else if (cmd == "sit") {                      // sit|First|object: take a free seat in it (the other poseball)
        key k = npc_named(llList2String(f, 1));
        if (k != NULL_KEY) {
            stop_dance(llList2String(f, 1), k);
            osNpcSit(k, (key)llList2String(f, 2), OS_NPC_SIT_NOW);
        }
    } else if (cmd == "stand") {                    // stand|First
        key k = npc_named(llList2String(f, 1));
        if (k != NULL_KEY) {
            stop_dance(llList2String(f, 1), k);
            osNpcStand(k);
        }
    } else if (cmd == "dance") {                    // dance|First|animation (one in this object's contents)
        string first = llList2String(f, 1);
        string anim = llList2String(f, 2);
        key k = npc_named(first);
        if (k != NULL_KEY && llGetInventoryType(anim) == INVENTORY_ANIMATION) {
            stop_dance(first, k);
            osNpcPlayAnimation(k, anim);
            dancing += [first, anim];
        }
    } else if (cmd == "still") {                    // still|First: stop dancing
        string first = llList2String(f, 1);
        stop_dance(first, npc_named(first));
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
        post("/heard", llGetRegionName() + "|" + name + "|" + (string)at.x + "|" + (string)at.y + "|" + (string)at.z + "|" + message);
    }

    timer() {
        key owner = llGetOwner();
        string here = "0";
        vector at = ZERO_VECTOR;
        string seat = "";
        if (llGetAgentSize(owner) != ZERO_VECTOR) {
            here = "1";
            list d = llGetObjectDetails(owner, [OBJECT_POS, OBJECT_ROOT]);
            at = llList2Vector(d, 0);
            key root = llList2Key(d, 1);            // what they're sitting on (themselves when standing)
            if (root != owner && root != NULL_KEY)
                seat = "&seat=" + (string)root + "&seatname=" + llEscapeURL(llKey2Name(root));
        }
        llHTTPRequest(BRIDGE + "/poll?region=" + llEscapeURL(llGetRegionName()) + "&here=" + here + "&x=" + (string)at.x +
                      "&y=" + (string)at.y + "&z=" + (string)at.z + seat, [HTTP_METHOD, "GET", HTTP_BODY_MAXLENGTH, 16384], "");
    }

    http_response(key request, integer status, list meta, string body) {
        if (status != 200 || body == "") return;
        list lines = llParseString2List(body, ["\n"], []);
        integer i;
        integer n = llGetListLength(lines);
        for (i = 0; i < n; ++i) do_line(llList2String(lines, i));
    }
}
