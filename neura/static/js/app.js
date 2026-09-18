const tabs = [
    ...document.querySelectorAll('.tabs button')
];

const forms = [
    ...document.querySelectorAll('.auth-form')
];


// ===============================
// TAB SWITCHING
// ===============================

function showTab(name) {
    tabs.forEach(button => {
        button.classList.toggle(
            'active',
            button.dataset.tab === name
        );
    });

    forms.forEach(form => {
        form.classList.toggle(
            'active',
            form.id === name
        );
    });
}

document.querySelectorAll('[data-tab]').forEach(button => {
    button.addEventListener('click', () => {
        showTab(button.dataset.tab);
    });
});

document.querySelectorAll('[data-open]').forEach(button => {
    button.addEventListener('click', () => {
        showTab(button.dataset.open);

        const authSection = document.getElementById('auth');

        if (authSection) {
            authSection.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});


// ===============================
// SIGNUP
// ===============================

const signupForm = document.getElementById('signup');

if (signupForm) {

    signupForm.addEventListener('submit', async function(event) {

        event.preventDefault();

        const emailInput =
            signupForm.querySelector('input[type="email"]');

        const passwordInput =
            signupForm.querySelector('input[type="password"]');

        const email = emailInput
            ? emailInput.value.trim()
            : '';

        const password = passwordInput
            ? passwordInput.value
            : '';

        if (!email || !password) {
            alert('Please enter email and password.');
            return;
        }

        try {

            const response = await fetch('/api/signup', {
                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            const result = await response.json();

            if (result.success) {

                alert(
                    result.message ||
                    'Account created successfully!'
                );

                showTab('login');

            } else {

                alert(
                    result.error ||
                    'Signup failed.'
                );
            }

        } catch (error) {

            console.error('Signup error:', error);

            alert(
                'Unable to connect to the server.'
            );
        }

    });
}


// ===============================
// LOGIN
// ===============================

const loginForm = document.getElementById('login');

if (loginForm) {

    loginForm.addEventListener('submit', async function(event) {

        event.preventDefault();

        const inputs =
            loginForm.querySelectorAll('input');

        const emailInput =
            loginForm.querySelector('input[type="email"]');

        const passwordInput =
            loginForm.querySelector('input[type="password"]');

        const email = emailInput
            ? emailInput.value.trim()
            : '';

        const password = passwordInput
            ? passwordInput.value
            : '';

        console.log('Login email:', email);
        console.log(
            'Password entered:',
            password ? 'YES' : 'NO'
        );

        if (!email || !password) {

            alert(
                'Please enter email and password.'
            );

            return;
        }

        try {

            const response = await fetch('/api/login', {

                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                })

            });

            const result = await response.json();

            console.log('Login response:', result);

            if (result.success) {

                alert(
                    result.message ||
                    'Login successful!'
                );

                window.location.href = '/home';

            } else {

                alert(
                    result.error ||
                    'Login failed.'
                );
            }

        } catch (error) {

            console.error(
                'Login error:',
                error
            );

            alert(
                'Unable to connect to the server.'
            );
        }

    });
}