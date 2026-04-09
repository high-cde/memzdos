const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(60,window.innerWidth/window.innerHeight,0.1,1000);
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setSize(window.innerWidth,window.innerHeight);
document.body.appendChild(renderer.domElement);
camera.position.z=30;

const nodes={};
const ws=new WebSocket("ws://"+location.hostname+":8000/ws");

ws.onmessage=(event)=>{
    const data=JSON.parse(event.data);
    if(!data.viz3d) return;
    data.viz3d.nodes.forEach(n=>{
        if(!nodes[n.id]){
            const g=new THREE.SphereGeometry(0.4,16,16);
            const m=new THREE.MeshBasicMaterial({color:0x00ff00});
            const mesh=new THREE.Mesh(g,m);
            mesh.position.set(n.x,n.y,n.z);
            scene.add(mesh);
            nodes[n.id]=mesh;
        }
    });
    ws.send("step");
};

function animate(){
    requestAnimationFrame(animate);
    scene.rotation.y+=0.002;
    renderer.render(scene,camera);
}
animate();
