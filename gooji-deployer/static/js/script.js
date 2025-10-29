document.addEventListener('DOMContentLoaded', () => {
  // --- Firebase & Auth State ---
  const auth = firebase.auth();
  let currentUser = null;
  let idToken = null;

  // --- DOM Elements ---
  const authSection = document.getElementById('authSection');
  const loginModal = document.getElementById('loginModal');
  const profileModal = document.getElementById('profileModal');
  const projectsSection = document.getElementById('projectsSection');
  const projectsList = document.getElementById('projectsList');
  const deploySection = document.getElementById('deploySection');

  // --- UI Update Functions ---
  const updateAuthUI = (user) => {
    if (user) {
      authSection.innerHTML = `
        <div class="relative">
          <button onclick="toggleProfileMenu()" class="flex items-center space-x-2 text-gray-700 font-medium hover:text-indigo-600">
            <i class="fas fa-user-circle text-2xl"></i>
            <span class="hidden md:block">${user.displayName || user.email}</span>
            <i class="fas fa-chevron-down text-xs"></i>
          </button>
          <div id="profileMenu" class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-50 hidden">
            <a href="#" onclick="openProfileModal(); return false;" class="block px-4 py-2 text-gray-700 hover:bg-gray-100">My Profile</a>
            <a href="#" onclick="showProjects(); return false;" class="block px-4 py-2 text-gray-700 hover:bg-gray-100">My Vercel Projects</a>
            <hr class="my-2">
            <a href="#" onclick="logout(); return false;" class="block px-4 py-2 text-gray-700 hover:bg-gray-100">Logout</a>
          </div>
        </div>
      `;
      projectsSection.classList.remove('hidden');
    } else {
      authSection.innerHTML = `
        <button onclick="openLoginModal()" class="bg-indigo-600 text-white font-semibold px-6 py-2 rounded-lg hover:bg-indigo-700 transition">
          Login
        </button>
      `;
      projectsSection.classList.add('hidden');
    }
  };

  // --- Auth Listeners ---
  auth.onAuthStateChanged(async (user) => {
    currentUser = user;
    if (user) {
      idToken = await user.getIdToken();
      // Fetch user profile from our backend to get username
      const profileRes = await fetch('/api/user/profile', {
        headers: { 'Authorization': `Bearer ${idToken}` }
      });
      const profileData = await profileRes.json();
      if (profileData.success) {
        user.displayName = profileData.data.username;
      }
    } else {
      idToken = null;
    }
    updateAuthUI(user);
  });

  // --- Auth Functions ---
  window.openLoginModal = () => loginModal.classList.remove('hidden');
  window.closeLoginModal = () => loginModal.classList.add('hidden');
  window.openProfileModal = async () => {
    if (!currentUser) return;
    // Fetch profile data to populate form
    const profileRes = await fetch('/api/user/profile', {
      headers: { 'Authorization': `Bearer ${idToken}` }
    });
    const profileData = await profileRes.json();
    if (profileData.success) {
      document.getElementById('profileUsername').value = profileData.data.username;
      document.getElementById('profileEmail').value = profileData.data.email;
    }
    profileModal.classList.remove('hidden');
  };
  window.closeProfileModal = () => profileModal.classList.add('hidden');
  window.toggleProfileMenu = () => {
    const menu = document.getElementById('profileMenu');
    menu.classList.toggle('hidden');
  };
  window.logout = () => auth.signOut();

  // --- Form Handlers ---
  document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const identifier = document.getElementById('loginIdentifier').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
      // Firebase Auth login dengan email
      await auth.signInWithEmailAndPassword(identifier, password);
      closeLoginModal();
    } catch (error) {
      // Jika gagal, coba cari email berdasarkan username (memerlukan backend)
      // Untuk kesederhanaan, kita asumsikan user login dengan email.
      // Implementasi username login memerlukan endpoint tambahan di backend.
      alert('Login failed: ' + error.message);
    }
  });

  document.getElementById('profileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('profileUsername').value;
    const password = document.getElementById('profilePassword').value;
    
    const updateData = { username };
    if (password) {
      updateData.password = password;
    }

    const res = await fetch('/api/user/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${idToken}`
      },
      body: JSON.stringify(updateData)
    });

    const result = await res.json();
    if (result.success) {
      alert('Profile updated successfully!');
      closeProfileModal();
      // Refresh auth state to update display name
      auth.onAuthStateChanged(() => {}); // Trigger re-evaluation
    } else {
      alert('Failed to update profile: ' + result.error);
    }
  });

  // --- Projects Management ---
  window.showProjects = async () => {
    if (!currentUser) return;
    
    projectsList.innerHTML = '<p class="text-center text-gray-500">Loading projects...</p>';
    deploySection.classList.add('hidden'); // Sembunyikan form deploy saat lihat proyek

    const res = await fetch('/api/vercel/projects', {
      headers: { 'Authorization': `Bearer ${idToken}` }
    });
    const result = await res.json();

    if (result.success) {
      if (result.data.length === 0) {
        projectsList.innerHTML = '<p class="text-center text-gray-500">You have no Vercel projects yet.</p>';
      } else {
        projectsList.innerHTML = result.data.map(project => `
          <div class="flex justify-between items-center p-4 border rounded-lg">
            <div>
              <h4 class="font-semibold">${project.name}</h4>
              <a href="${project.url}" target="_blank" class="text-indigo-600 hover:underline text-sm">${project.url}</a>
            </div>
            <button onclick="deleteProject('${project.id}')" class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition">
              <i class="fas fa-trash"></i> Delete
            </button>
          </div>
        `).join('');
      }
    } else {
      projectsList.innerHTML = `<p class="text-center text-red-500">Failed to load projects: ${result.error}</p>`;
    }
  };

  window.deleteProject = async (projectId) => {
    if (!confirm('Are you sure you want to delete this project from our records? This will not delete it from Vercel.')) {
      return;
    }

    const res = await fetch(`/api/vercel/projects/${projectId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${idToken}` }
    });

    const result = await res.json();
    if (result.success) {
      alert('Project removed from your list.');
      showProjects(); // Refresh the list
    } else {
      alert('Failed to delete project: ' + result.error);
    }
  };

  // --- Original Deployment Logic (Modified) ---
  const form = document.getElementById('deployForm');
  const domainInput = document.getElementById('domain');
  const fileInput = document.getElementById('file');
  const domainError = document.getElementById('domainError');
  const fileError = document.getElementById('fileError');
  const loadingSpinner = document.getElementById('loadingSpinner');
  const submitBtn = document.getElementById('submitBtn');
  const gocloudOption = document.getElementById('gocloudOption');
  const vercelOption = document.getElementById('vercelOption');
  const popupModal = document.getElementById('popupModal');
  const popupContent = document.getElementById('popupContent');
  const popupContentWrapper = document.getElementById('popupContentWrapper');
  const closePopup = document.getElementById('closePopup');
  const fileNameText = document.getElementById('fileName');
  const welcomeModal = document.getElementById('welcomeModal');
  const closeWelcomePopup = document.getElementById('closeWelcomePopup');
  const joinChannelBtn = document.getElementById('joinChannelBtn');

  // ... (Sisanya adalah logika orisinal Anda untuk deployment, popup, dll.)
  // Saya akan menempelkan semuanya di sini dan memodifikasi bagian pengiriman form.

  // Deployment target selection
  function updateDeploymentTarget() {
    const selectedTarget = document.querySelector('input[name="deploymentTarget"]:checked').value;
    if (selectedTarget === 'vercel') {
      gocloudOption.classList.remove('selected');
      vercelOption.classList.add('selected');
    } else {
      gocloudOption.classList.add('selected');
      vercelOption.classList.remove('selected');
    }
  }
  updateDeploymentTarget();
  document.querySelectorAll('input[name="deploymentTarget"]').forEach(radio => {
    radio.addEventListener('change', updateDeploymentTarget);
  });

  // Welcome Popup
  if (!sessionStorage.getItem('welcomePopupShown')) {
    setTimeout(() => {
      welcomeModal.classList.remove('hidden');
      document.body.classList.add('popup-open');
    }, 1500);
  }
  function closeWelcomeModal() {
    const wrapper = welcomeModal.querySelector('.animate-fade-in-scale');
    wrapper.classList.remove('animate-fade-in-scale');
    wrapper.classList.add('animate-fade-out-scale');
    wrapper.addEventListener('animationend', () => {
      welcomeModal.classList.add('hidden');
      if (popupModal.classList.contains('hidden')) {
        document.body.classList.remove('popup-open');
      }
    }, { once: true });
    sessionStorage.setItem('welcomePopupShown', 'true');
  }
  closeWelcomePopup.addEventListener('click', closeWelcomeModal);
  joinChannelBtn.addEventListener('click', closeWelcomeModal);
  welcomeModal.addEventListener('click', (e) => { if (e.target === welcomeModal) closeWelcomeModal(); });

  // File Input Name Display
  fileInput.addEventListener('change', function() {
    fileNameText.textContent = this.files.length ? this.files[0].name : 'No file';
  });

  // Result Popup Logic
  function closePopupWithAnimation() {
    popupContentWrapper.classList.remove('animate-fade-in-scale');
    popupContentWrapper.classList.add('animate-fade-out-scale');
    popupContentWrapper.addEventListener('animationend', () => {
      popupModal.classList.add('hidden');
      document.body.classList.remove('popup-open');
    }, { once: true });
  }
  closePopup.addEventListener('click', closePopupWithAnimation);
  popupModal.addEventListener('click', (e) => { if (e.target === popupModal) closePopupWithAnimation(); });

  // Form Validation
  const validateDomain = (domain) => /^[a-z0-9-]{3,64}$/.test(domain);
  const validateFile = (file) => file && ['.html', '.zip', '.js', '.css', '.json'].some(ext => file.name.toLowerCase().endsWith(ext));

  // MODIFIED: Form Submission Logic
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentUser) {
      alert('Please login to deploy projects.');
      openLoginModal();
      return;
    }

    domainError.classList.add('hidden');
    fileError.classList.add('hidden');

    const domain = domainInput.value.trim().toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    const file = fileInput.files[0];
    const deploymentTarget = document.querySelector('input[name="deploymentTarget"]:checked').value;
    
    let valid = true;
    if (!validateDomain(domain)) { domainError.classList.remove('hidden'); valid = false; }
    if (!validateFile(file)) { fileError.classList.remove('hidden'); valid = false; }
    if (!valid) return;

    loadingSpinner.classList.remove('hidden');
    submitBtn.disabled = true;

    try {
      let result;
      const formData = new FormData();
      formData.append('domain', domain);
      formData.append('file', file);

      const endpoint = deploymentTarget === 'gocloud' ? '/api/deploy/gocloud' : '/api/deploy/vercel';
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${idToken}`
        },
        body: formData
      });
      
      const json = await response.json();
      
      if (!json.success) {
        throw new Error(json.error || `Deployment to ${deploymentTarget} failed.`);
      }
      
      showSuccessPopup(json.url, deploymentTarget);
      
    } catch (error) {
      showErrorPopup(error.message);
    } finally {
      loadingSpinner.classList.add('hidden');
      submitBtn.disabled = false;
      form.reset();
      fileNameText.textContent = 'No file';
      updateDeploymentTarget();
    }
  });

  // Popup Display Functions
  function showSuccessPopup(url, platform) {
    const qrApiUrl = `https://apii.baguss.web.id/tools/toqr?apikey=bagus&text=${encodeURIComponent(url)}`;
    popupContentWrapper.classList.remove('animate-fade-out-scale');
    popupContentWrapper.classList.add('animate-fade-in-scale');
    popupContent.innerHTML = `
      <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100"><i class="fas fa-check text-2xl text-green-600"></i></div>
      <div class="mt-3 text-center sm:mt-5">
        <h3 class="text-lg leading-6 font-bold text-gray-900">Deployment Successful!</h3>
        <p class="text-sm text-gray-500 mt-1">Deployed to ${platform}</p>
        <div class="mt-4">
          <img src="${qrApiUrl}" alt="QR code for ${url}" class="w-32 h-32 rounded-lg border-2 border-gray-200 shadow-sm mx-auto"/>
          <div class="relative rounded-md shadow-sm mt-4">
            <input type="text" id="deployedUrl" readonly value="${url}" class="block w-full rounded-md border-gray-300 bg-gray-100 text-sm p-2 text-center text-gray-600 focus:ring-0 focus:border-gray-300" style="word-break: break-all;">
          </div>
        </div>
        <p class="text-xs text-gray-500 mt-2">Site is live in 1-5 mins.</p>
      </div>
      <div class="mt-5 sm:mt-6">
        <button type="button" id="copyUrlBtn" class="inline-flex w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:text-sm">Copy Link</button>
      </div>
    `;
    document.getElementById('copyUrlBtn').addEventListener('click', (e) => {
      const urlInput = document.getElementById('deployedUrl');
      const copyBtn = e.currentTarget;
      navigator.clipboard.writeText(urlInput.value).then(() => {
        copyBtn.textContent = 'Copied!';
        copyBtn.classList.add('bg-green-600', 'hover:bg-green-700');
        copyBtn.classList.remove('bg-indigo-600', 'hover:bg-indigo-700');
        setTimeout(() => {
          copyBtn.textContent = 'Copy Link';
          copyBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
          copyBtn.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
        }, 2000);
      });
    });
    popupModal.classList.remove('hidden');
    document.body.classList.add('popup-open');
  }
  function showErrorPopup(errorMessage) {
    popupContentWrapper.classList.remove('animate-fade-out-scale');
    popupContentWrapper.classList.add('animate-fade-in-scale');
    popupContent.innerHTML = `
      <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100"><i class="fas fa-times text-2xl text-red-600"></i></div>
      <div class="mt-3 text-center sm:mt-5">
        <h3 class="text-lg leading-6 font-bold text-gray-900">An Error Occurred</h3>
        <div class="mt-2"><p class="text-sm text-gray-600 break-words">${errorMessage}</p></div>
      </div>
    `;
    popupModal.classList.remove('hidden');
    document.body.classList.add('popup-open');
  }
});