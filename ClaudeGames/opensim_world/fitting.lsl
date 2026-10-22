// The Fitting Room: a platform owned by Hollow Tailor. The Tailor is sat on it (standing upright, facing the camera
// the platform sets), then changed into each furry avatar in turn with RestrainedLove commands to its viewer; each
// look is saved as a notecard and reported to the computer that launched the world, which takes a picture first.
// The looks to try (folder names under #RLV) are filled in by tailor.py.
string BRIDGE = "http://127.0.0.1:9180";
list LOOKS = [/*LOOKS*/];
float WAIT = /*SECONDS*/;
integer i = -2;                  // -2: waiting for the Tailor, -1: letting its inventory load, then the looks
key saving;
integer REPLIES = 4711;          // the viewer's RestrainedLove answers come back on this channel

post(string path, string body) {
    llHTTPRequest(BRIDGE + path, [HTTP_METHOD, "POST", HTTP_MIMETYPE, "text/plain;charset=utf-8"], body);
}

dress() {
    string look = llList2String(LOOKS, i);
    llOwnerSay("@detach=force");
    llOwnerSay("@remoutfit=force");
    llSleep(4.0);                                   // let the last look come off first
    llOwnerSay("@attachall:" + look + "=force");
    post("/say", "trying on " + look);
}

default {
    state_entry() {
        llSetText("Fitting Room", <1.0, 0.9, 0.95>, 0.6);
        llSitTarget(<0.0, 0.0, 1.25>, ZERO_ROTATION);          // standing on the platform, facing +x
        llSetCameraEyeOffset(<3.0, 0.0, 1.55>);                 // the camera in front, looking back at the face
        llSetCameraAtOffset(<0.0, 0.0, 1.35>);
        llListen(REPLIES, "", llGetOwner(), "");
        llSetTimerEvent(5.0);
    }

    listen(integer channel, string name, key id, string message) {
        post("/say", "viewer: " + llGetSubString(message, 0, 300));
    }

    changed(integer change) {
        if (change & CHANGED_LINK) {
            key sitter = llAvatarOnSitTarget();
            if (sitter == llGetOwner()) llRequestPermissions(sitter, PERMISSION_TRIGGER_ANIMATION);
        }
    }

    run_time_permissions(integer perms) {
        if (perms & PERMISSION_TRIGGER_ANIMATION) {           // granted without asking to what you sit on
            llStopAnimation("sit");
            llStartAnimation("stand");
        }
    }

    timer() {
        key o = llGetOwner();
        if (llGetAgentSize(o) == ZERO_VECTOR) return;           // the Tailor isn't here yet
        if (i == -2) {
            post("/say", "the Tailor is here");
            llOwnerSay("@setenv_daytime:0.5=force");            // midday, for the pictures
            llOwnerSay("@sit:" + (string)llGetKey() + "=force");
            llOwnerSay("@versionnum=" + (string)REPLIES);
            llOwnerSay("@getinv=" + (string)REPLIES);         // also makes the viewer load the #RLV folders
            i = -1;
            llSetTimerEvent(30.0);                              // its inventory loads meanwhile
            return;
        }
        if (i == -1) {
            i = 0;
            dress();
            llSetTimerEvent(WAIT);
            return;
        }
        llSetTimerEvent(0.0);
        llOwnerSay("@getattach=" + (string)REPLIES);          // what's on (reported in the log)
        llSleep(2.0);
        string look = llList2String(LOOKS, i);
        osAgentSaveAppearance(o, look);
        // the reply comes back once the picture's been taken
        saving = llHTTPRequest(BRIDGE + "/outfit", [HTTP_METHOD, "POST", HTTP_MIMETYPE, "text/plain;charset=utf-8"],
                               look + "|" + (string)llGetInventoryKey(look));
    }

    http_response(key request, integer status, list meta, string body) {
        if (request != saving) return;
        i += 1;
        if (i >= llGetListLength(LOOKS)) {
            llOwnerSay("@detach=force");
            llOwnerSay("@unsit=force");
            post("/done", "");
            return;
        }
        dress();
        llSetTimerEvent(WAIT);
    }
}
