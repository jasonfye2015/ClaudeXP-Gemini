// The 3D world for Second Life. Python (the viewer) builds everything in it through the functions below and
// hears about clicks and drags through `bridge`. Objects are kept by tag in `objs`.
import QtQuick
import QtQuick3D

Item {
    id: root
    property real t: 0
    property real camYaw: 0
    property real camX: 0
    property real camY: 0
    property real camZ: 0
    property var objs: ({})
    NumberAnimation on t { from: 0; to: 100000; duration: 100000000; loops: Animation.Infinite; running: true }

    View3D {
        id: view
        anchors.fill: parent
        environment: SceneEnvironment {
            id: env
            backgroundMode: SceneEnvironment.Color
            clearColor: "#9CC8F0"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
            fog: Fog { id: fog; enabled: true; color: "#C8DCF0"; depthEnabled: true; depthNear: 2600; depthFar: 9000 }
        }
        PerspectiveCamera { id: cam; fieldOfView: 55; clipNear: 5; clipFar: 30000; position: Qt.vector3d(0, 300, 800) }
        DirectionalLight { id: sun; eulerRotation.x: -48; eulerRotation.y: -35; brightness: 1.0; castsShadow: true
                           shadowMapQuality: Light.ShadowMapQualityHigh; shadowFactor: 45; shadowMapFar: 4000
                           ambientColor: "#505860" }
        DirectionalLight { id: fill; eulerRotation.x: -18; eulerRotation.y: 150; brightness: 0.35 }
        Node { id: world }
        Node { id: things }
        Node { id: people }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        property real lastX: 0
        property real lastY: 0
        property bool moved: false
        onPressed: (m) => { lastX = m.x; lastY = m.y; moved = false; bridge.pressed(m.x, m.y, m.button) }
        onPositionChanged: (m) => {
            var dx = m.x - lastX, dy = m.y - lastY;
            if (Math.abs(dx) + Math.abs(dy) > 0) { if (Math.abs(m.x - lastX) + Math.abs(m.y - lastY) > 2) moved = true }
            lastX = m.x; lastY = m.y;
            bridge.dragged(dx, dy, m.buttons)
        }
        onReleased: (m) => {
            var r = view.pick(m.x, m.y);
            bridge.released(r.objectHit ? r.objectHit.objectName : "", r.scenePosition.x, r.scenePosition.y,
                            r.scenePosition.z, m.x, m.y, m.button)
        }
        onDoubleClicked: (m) => {
            var r = view.pick(m.x, m.y);
            bridge.doubleClicked(r.objectHit ? r.objectHit.objectName : "", r.scenePosition.x, r.scenePosition.y,
                                 r.scenePosition.z)
        }
        onWheel: (w) => bridge.wheel(w.angleDelta.y)
    }

    function layerNode(name) { return name === "world" ? world : name === "things" ? things : people }
    function spawn(qml, tag, where) {          // "" when it worked, else what went wrong
        drop(tag);
        try {
            var o = Qt.createQmlObject(qml, layerNode(where), tag);
            objs[tag] = o;
            return "";
        } catch (e) {
            return e.qmlErrors ? JSON.stringify(e.qmlErrors).substring(0, 600) : String(e);
        }
    }
    function drop(tag) { if (objs[tag]) { objs[tag].destroy(); delete objs[tag]; } }
    function dropPrefix(prefix) {
        var p = prefix ? String(prefix) : "";
        for (var k in objs) if (k.indexOf(p) === 0) { objs[k].destroy(); delete objs[k]; }
    }
    function dropAll() {
        for (var k in objs) objs[k].destroy();
        objs = ({});
    }
    function apply(rows) {          // avatars: [tag, x, y, z, yaw, walking, dance, sitting, flying, typing]
        for (var i = 0; i < rows.length; i++) {
            var r = rows[i], o = objs[r[0]];
            if (!o) continue;
            o.position = Qt.vector3d(r[1], r[2], r[3]);
            o.eulerRotation = Qt.vector3d(0, r[4], 0);
            o.walking = r[5]; o.dance = r[6]; o.sitting = r[7]; o.flying = r[8]; o.typing = r[9];
        }
    }
    function place(tag, x, y, z, rx, ry, rz) {
        var o = objs[tag];
        if (!o) return;
        o.position = Qt.vector3d(x, y, z);
        o.eulerRotation = Qt.vector3d(rx, ry, rz);
    }
    function setProp(tag, name, value) { if (objs[tag]) objs[tag][name] = value }
    function camera(x, y, z, pitch, yaw) {
        cam.position = Qt.vector3d(x, y, z);
        cam.eulerRotation = Qt.vector3d(pitch, yaw, 0);
        root.camYaw = yaw;
        root.camX = x; root.camY = y; root.camZ = z;
    }
    function setEnv(e) {
        env.clearColor = e.sky;
        fog.color = e.fog; fog.depthNear = e.fogNear; fog.depthFar = e.fogFar;
        sun.color = e.sun; sun.brightness = e.sunBright; sun.ambientColor = e.ambient;
        sun.eulerRotation = Qt.vector3d(e.sunPitch, e.sunYaw, 0);
        fill.brightness = e.fill;
    }
}
