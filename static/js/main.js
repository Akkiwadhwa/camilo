// static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    // Form validation
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();

            if (!username || !password) {
                e.preventDefault();
                alert('Please fill in all fields');
            }
        });
    }

    // Add hover effect to action cards
    document.querySelectorAll('.action-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.boxShadow = '0 8px 12px rgba(0,0,0,0.1)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.boxShadow = '0 4px 6px rgba(0,0,0,0.05)';
        });
    });

    // Handle alert dismissal
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    });
});