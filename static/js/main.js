document.addEventListener('DOMContentLoaded', function() {
    // Dark Mode Toggle
    const toggleBtn = document.getElementById('darkModeToggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });

        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        }
    }

    // Pomodoro Timer
    let timeLeft = 25 * 60;
    let timerId = null;
    const display = document.getElementById('timerDisplay');
    
    if (display) {
        function updateDisplay() {
            const mins = Math.floor(timeLeft / 60);
            const secs = timeLeft % 60;
            display.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }

        document.getElementById('startTimer').addEventListener('click', () => {
            if (timerId) return;
            timerId = setInterval(() => {
                timeLeft--;
                updateDisplay();
                if (timeLeft <= 0) {
                    clearInterval(timerId);
                    alert("Time's up! Take a break.");
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
            updateDisplay();
        });
    }

    // Chart.js
    const ctx = document.getElementById('progressChart');
    if (ctx) {
        fetch('/api/stats')
            .then(res => res.json())
            .then(data => {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Tasks Completed',
                            data: data.data,
                            borderColor: '#0d6efd',
                            tension: 0.1
                        }]
                    },
                    options: {
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            });
    }
    
    // AI Recommendations
    const recDiv = document.getElementById('recommendations');
    if (recDiv) {
        fetch('/api/recommendations')
            .then(res => res.json())
            .then(data => {
                let html = '<ul class="mb-0">';
                data.forEach(rec => {
                    html += `<li>${rec}</li>`;
                });
                html += '</ul>';
                recDiv.innerHTML = html;
            });
    }
});
