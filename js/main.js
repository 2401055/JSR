document.addEventListener('DOMContentLoaded', function() {
    // State Management
    let tasks = JSON.parse(localStorage.getItem('study_tasks')) || [];
    let user = localStorage.getItem('study_user') || null;

    // Elements
    const authSection = document.getElementById('authSection');
    const mainDashboard = document.getElementById('mainDashboard');
    const loginBtn = document.getElementById('loginBtn');
    const usernameInput = document.getElementById('usernameInput');
    const displayName = document.getElementById('displayName');
    const taskList = document.getElementById('taskList');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const motivationalMsg = document.getElementById('motivationalMsg');

    // Init
    if (user) {
        showDashboard();
    }

    loginBtn.addEventListener('click', () => {
        const name = usernameInput.value.trim();
        if (name) {
            user = name;
            localStorage.setItem('study_user', name);
            showDashboard();
        }
    });

    function showDashboard() {
        authSection.classList.add('d-none');
        mainDashboard.classList.remove('d-none');
        displayName.textContent = user;
        updateUI();
        initChart();
    }

    // Task Management
    document.getElementById('saveTaskBtn').addEventListener('click', () => {
        const newTask = {
            id: Date.now(),
            subject: document.getElementById('taskSubject').value,
            title: document.getElementById('taskTitle').value,
            deadline: document.getElementById('taskDeadline').value,
            difficulty: document.getElementById('taskDifficulty').value,
            priority: parseInt(document.getElementById('taskPriority').value),
            hours: parseFloat(document.getElementById('taskHours').value),
            completed: false,
            scheduledDate: null
        };

        tasks.push(newTask);
        saveTasks();
        updateUI();
        bootstrap.Modal.getInstance(document.getElementById('addTaskModal')).hide();
    });

    function saveTasks() {
        localStorage.setItem('study_tasks', JSON.stringify(tasks));
    }

    function updateUI() {
        // Filter for today (simple logic: all uncompleted or scheduled for today)
        const today = new Date().toISOString().split('T')[0];
        
        taskList.innerHTML = '';
        tasks.forEach(task => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <div>
                    <h6 class="mb-0 ${task.completed ? 'text-decoration-line-through text-muted' : ''}">${task.title}</h6>
                    <small class="badge bg-info text-dark">${task.subject}</small>
                    <small class="text-muted">| Difficulty: ${task.difficulty} | Priority: ${task.priority}</small>
                    ${task.scheduledDate ? `<br><small class="text-success">Scheduled: ${task.scheduledDate}</small>` : ''}
                </div>
                <div>
                    <button class="btn btn-sm ${task.completed ? 'btn-secondary' : 'btn-success'}" onclick="toggleTask(${task.id})">
                        ${task.completed ? 'Undo' : 'Done'}
                    </button>
                    <button class="btn btn-sm btn-outline-danger ms-1" onclick="deleteTask(${task.id})">×</button>
                </div>
            `;
            taskList.appendChild(item);
        });

        // Progress
        const completed = tasks.filter(t => t.completed).length;
        const total = tasks.length;
        const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
        
        progressBar.style.width = percent + '%';
        progressBar.textContent = percent + '%';
        progressText.textContent = `Completed: ${completed} | Pending: ${total - completed}`;

        // Motivation
        const msgs = ["Keep going!", "You've got this!", "Focus on the goal.", "Small steps every day."];
        motivationalMsg.textContent = `"${msgs[Math.floor(Math.random() * msgs.length)]}"`;

        updateRecommendations();
    }

    window.toggleTask = (id) => {
        tasks = tasks.map(t => t.id === id ? {...t, completed: !t.completed} : t);
        saveTasks();
        updateUI();
    };

    window.deleteTask = (id) => {
        tasks = tasks.filter(t => t.id !== id);
        saveTasks();
        updateUI();
    };

    // Smart Planner Logic
    document.getElementById('generatePlanBtn').addEventListener('click', () => {
        const sorted = [...tasks].filter(t => !t.completed).sort((a, b) => {
            if (a.deadline !== b.deadline) return new Date(a.deadline) - new Date(b.deadline);
            return a.priority - b.priority;
        });

        let currentDate = new Date();
        let dailyHours = 0;
        const limit = 4;

        sorted.forEach(task => {
            if (dailyHours + task.hours > limit && dailyHours > 0) {
                currentDate.setDate(currentDate.getDate() + 1);
                dailyHours = 0;
            }
            task.scheduledDate = currentDate.toISOString().split('T')[0];
            dailyHours += task.hours;
        });

        tasks = [...tasks.filter(t => t.completed), ...sorted];
        saveTasks();
        updateUI();
        alert('Smart Plan Generated!');
    });

    // Timer
    let timeLeft = 25 * 60;
    let timerId = null;
    const timerDisplay = document.getElementById('timerDisplay');
    
    document.getElementById('startTimer').addEventListener('click', () => {
        if (timerId) return;
        timerId = setInterval(() => {
            timeLeft--;
            const m = Math.floor(timeLeft / 60);
            const s = timeLeft % 60;
            timerDisplay.textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
            if (timeLeft <= 0) {
                clearInterval(timerId);
                alert("Time's up!");
            }
        }, 1000);
    });

    document.getElementById('pauseTimer').addEventListener('click', () => {
        clearInterval(timerId);
        timerId = null;
    });

    document.getElementById('resetTimer').addEventListener('click', () => {
        clearInterval(timerId);
        timerId = null;
        timeLeft = 25 * 60;
        timerDisplay.textContent = "25:00";
    });

    // Recommendations
    function updateRecommendations() {
        const recDiv = document.getElementById('recommendations');
        const pending = tasks.filter(t => !t.completed);
        const hard = pending.filter(t => t.difficulty === 'hard');
        
        let html = '<ul class="mb-0">';
        if (hard.length > 0) html += `<li>💡 You have ${hard.length} hard tasks. Do them first!</li>`;
        if (pending.length > 5) html += `<li>⏰ Heavy workload detected. Use the Smart Planner.</li>`;
        if (pending.length === 0) html += `<li>🌟 All done! Take a break.</li>`;
        html += '</ul>';
        recDiv.innerHTML = html;
    }

    // Chart
    function initChart() {
        const ctx = document.getElementById('progressChart');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Completion Trend',
                    data: [1, 2, 1, 4, 3, 0, 0],
                    borderColor: '#0d6efd'
                }]
            }
        });
    }

    // Dark Mode
    document.getElementById('darkModeToggle').addEventListener('click', () => {
        const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', theme);
    });
});
