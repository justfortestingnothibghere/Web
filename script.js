// Three.js 3D Background Animation
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById('threejs-bg').appendChild(renderer.domElement);

const geometry = new THREE.TorusKnotGeometry(10, 3, 100, 16);
const material = new THREE.MeshBasicMaterial({ color: 0x00ff88, wireframe: true });
const torusKnot = new THREE.Mesh(geometry, material);
scene.add(torusKnot);

camera.position.z = 20;

function animate() {
    requestAnimationFrame(animate);
    torusKnot.rotation.x += 0.01;
    torusKnot.rotation.y += 0.01;
    renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Vue App
new Vue({
    el: '#app',
    data: {
        showLogin: false,
        showSignup: false,
        loginUsername: '',
        loginPassword: '',
        signupUsername: '',
        signupEmail: '',
        signupPassword: '',
        referralCode: '',
        isLoggedIn: false,
        user: {},
        products: [],
        newProduct: { name: '', description: '', price: 0, type: '', demo_url: '' },
        showReferralModal: false,
        referralLink: '',
        users: []
    },
    methods: {
        async login() {
            try {
                const res = await axios.post('/api/login', { username: this.loginUsername, password: this.loginPassword });
                this.isLoggedIn = true;
                this.showLogin = false;
                this.user = res.data;
                this.fetchProducts();
                this.fetchUsers();
            } catch (err) {
                alert('Login failed');
            }
        },
        async signup() {
            try {
                const res = await axios.post('/api/signup', { username: this.signupUsername, email: this.signupEmail, password: this.signupPassword, referral_code: this.referralCode });
                this.showSignup = false;
                alert('Signup successful, please login');
            } catch (err) {
                alert('Signup failed');
            }
        },
        async logout() {
            await axios.get('/api/logout');
            this.isLoggedIn = false;
            this.user = {};
            this.users = [];
        },
        async fetchProducts() {
            const res = await axios.get('/api/products');
            this.products = res.data;
        },
        async addProduct() {
            await axios.post('/api/products', this.newProduct);
            this.fetchProducts();
            this.newProduct = { name: '', description: '', price: 0, type: '', demo_url: '' };
        },
        async showReferral() {
            const res = await axios.get('/api/referral');
            this.referralLink = res.data.referral_link;
            this.showReferralModal = true;
        },
        async requestCreator() {
            await axios.post('/api/request_creator');
            alert('Request sent');
            this.fetchUser();
        },
        async approveCreator(userId) {
            await axios.post(`/api/admin/approve_creator/${userId}`);
            this.fetchUsers();
        },
        async fetchUsers() {
            if (this.user.role === 'admin') {
                const res = await axios.get('/api/admin/users');
                this.users = res.data;
            }
        },
        async fetchUser() {
            try {
                const res = await axios.get('/api/user');
                this.user = res.data;
                this.isLoggedIn = true;
                this.fetchUsers();
            } catch {
                this.isLoggedIn = false;
            }
        }
    },
    mounted() {
        this.fetchProducts();
        this.fetchUser();
    }
});