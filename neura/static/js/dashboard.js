const plans = {
    Energetic: [
        ['Deep work: hardest subject', '45 min', 'High'],
        ['Problem-solving sprint', '30 min', 'High'],
        ['Quick recall', '15 min', 'Normal'],
        ['Reset + reflect', '10 min', 'Low']
    ],

    Happy: [
        ['Learn one new concept', '35 min', 'High'],
        ['Practice questions', '30 min', 'Normal'],
        ['Make compact notes', '20 min', 'Normal'],
        ['Review the win', '10 min', 'Low']
    ],

    Calm: [
        ['Read & understand one topic', '30 min', 'Normal'],
        ['Active recall', '20 min', 'Normal'],
        ['Flashcards', '15 min', 'Low'],
        ['Plan tomorrow', '10 min', 'Low']
    ],

    Tired: [
        ['Light revision', '20 min', 'Low'],
        ['Watch/review a concept', '20 min', 'Normal'],
        ['Flashcards', '15 min', 'Low'],
        ['Organize materials', '10 min', 'Low']
    ],

    Stressed: [
        ['Pick ONE important topic', '20 min', 'High'],
        ['Easy practice questions', '15 min', 'Normal'],
        ['Write 3 things you learned', '10 min', 'Low'],
        ['Review one small concept', '10 min', 'Low']
    ]
};


let state = {
    moods: [],
    tasks: [],
    sessions: []
};

let selectedMood = null;
let completed = 0;
let sessions = 0;


const $ = id => document.getElementById(id);

const toast = msg => {
    const t = $('toast');

    if (!t) return;

    t.textContent = msg;
    t.classList.add('show');

    setTimeout(() => {
        t.classList.remove('show');
    }, 1800);
};


async function api(url, opts = {}) {

    const r = await fetch(url, {
        headers: {
            'Content-Type': 'application/json'
        },
        ...opts
    });

    const d = await r.json().catch(() => ({}));

    if (!r.ok) {
        throw Error(d.error || 'Request failed');
    }

    return d;
}


/* ================================
   LOAD CLOUD DATA
================================ */

async function load() {

    try {

        state = await api('/api/state');

        completed = state.tasks.filter(x => x.done).length;

        sessions = state.sessions.length;

        updateStats();

        renderCustomTasks();

        renderHistory();

    } catch (e) {

        console.error('Load error:', e);

        toast('Cloud sync is not configured yet.');
    }
}


/* ================================
   STATISTICS
================================ */

function updateStats() {

    if ($('completedCount')) {
        $('completedCount').textContent = completed;
    }

    if ($('sessionCount')) {
        $('sessionCount').textContent = sessions;
    }

    if ($('streak')) {

        $('streak').textContent =
            Math.min(
                7,
                new Set(
                    state.moods.map(
                        x => (x.created_at || '').slice(0, 10)
                    )
                ).size
            );
    }
}


/* ================================
   AI NEXT BEST ACTION
================================ */

async function generateNextBestAction(mood, energy) {

    /*
       First try to find an unfinished custom task.
       This makes the AI recommendation related
       to the student's actual task.
    */

    let task = state.tasks.find(x => !x.done);

    let taskName;
    let priority;

    if (task) {

        taskName = task.title || task.name || 'Study your current subject';

        priority = task.priority || 'Normal';

    } else {

        /*
           If there is no custom task, use the first
           adaptive study activity as the task.
        */

        const fallbackPlan = plans[mood] || plans.Calm;

        taskName = fallbackPlan[0][0];

        priority = fallbackPlan[0][2];
    }


    /*
       Show a temporary message while AI is working.
    */

    $('adaptiveTitle').textContent = 'Neura is thinking…';

    $('adaptiveCopy').textContent =
        `Creating an adaptive study step for "${taskName}".`;


    try {

        const data = await api('/api/next-best-action', {

            method: 'POST',

            body: JSON.stringify({

                mood: mood,

                energy: energy,

                task: taskName,

                priority: priority

            })

        });


        if (data.success && data.recommendation) {

            $('adaptiveTitle').textContent =
                'AI-powered next best action';

            $('adaptiveCopy').textContent =
                data.recommendation;

        } else {

            throw new Error('AI recommendation unavailable');
        }


    } catch (error) {

        console.error('AI recommendation error:', error);

        /*
           Rule-based fallback.
           This means the planner still works even
           if the AI model is unavailable.
        */

        const fallbackPlan = plans[mood] || plans.Calm;

        $('adaptiveTitle').textContent =
            fallbackPlan[0][0];

        $('adaptiveCopy').textContent =
            `Start with this ${fallbackPlan[0][1]} ${mood.toLowerCase()}-friendly study activity.`;
    }
}


/* ================================
   MOOD PLAN
================================ */

function renderPlan(mood) {

    selectedMood = mood;

    $('planMood').textContent = mood + ' mode';

    $('moodLabel').textContent = mood + ' signal';


    const fill = {
        Energetic: 95,
        Happy: 80,
        Calm: 62,
        Tired: 28,
        Stressed: 42
    }[mood];


    $('energyFill').style.width = fill + '%';


    /*
       Show AI recommendation in the
       Next Best Action card.
    */

    generateNextBestAction(mood, fill);


    /*
       Keep the existing adaptive plan.
    */

    const list = plans[mood];


    $('taskList').innerHTML = list
        .map(
            (x, i) => `
                <div class="task">

                    <button
                        class="check"
                        data-plan="${i}">
                    </button>

                    <span class="task-name">
                        ${x[0]}
                    </span>

                    <span class="tag">
                        ${x[1]}
                    </span>

                    <span class="tag">
                        ${x[2]}
                    </span>

                </div>
            `
        )
        .join('');


    document
        .querySelectorAll('[data-plan]')
        .forEach(b => {

            b.onclick = () => {

                b.parentElement.classList.add('done');

                completed++;

                updateStats();

                toast('Adaptive step completed ✦');
            };

        });


    /*
       Save mood to Supabase.
    */

    api('/api/mood', {

        method: 'POST',

        body: JSON.stringify({

            mood: mood,

            energy: fill,

            context: 'dashboard'

        })

    })
        .then(load)
        .catch(error => {

            console.error('Mood save error:', error);

        });
}


/* ================================
   MOOD BUTTONS
================================ */

document
    .querySelectorAll('.mood')
    .forEach(b => {

        b.onclick = () => {

            document
                .querySelectorAll('.mood')
                .forEach(x =>
                    x.classList.remove('selected')
                );

            b.classList.add('selected');

            renderPlan(b.dataset.mood);

        };

    });


/* ================================
   REFRAME
================================ */

$('shufflePlan').onclick = () => {

    if (selectedMood) {

        renderPlan(selectedMood);

    } else {

        toast('Choose a mood first');
    }
};


/* ================================
   CUSTOM TASKS
================================ */

function renderCustomTasks() {

    const box = $('customTasks');

    if (!state.tasks.length) {

        box.innerHTML =
            '<div class="empty">No custom tasks yet. Add your first one.</div>';

        return;
    }


    box.innerHTML = state.tasks
        .map(
            t => `
                <div class="task ${t.done ? 'done' : ''}">

                    <button
                        class="check"
                        data-id="${t.id}">
                    </button>

                    <span class="task-name">
                        ${esc(t.title || t.name)}
                    </span>

                    <span class="tag">
                        ${esc(t.priority || 'Normal')}
                    </span>

                    <button
                        class="ghost"
                        data-del="${t.id}">
                        Delete
                    </button>

                </div>
            `
        )
        .join('');


    box
        .querySelectorAll('[data-id]')
        .forEach(b => {

            b.onclick = () =>
                toggleTask(b.dataset.id);

        });


    box
        .querySelectorAll('[data-del]')
        .forEach(b => {

            b.onclick = () =>
                deleteTask(b.dataset.del);

        });
}


/* ================================
   ESCAPE HTML
================================ */

const esc = s =>
    String(s).replace(
        /[&<>"']/g,
        c =>
            ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[c])
    );


/* ================================
   TOGGLE TASK
================================ */

async function toggleTask(id) {

    const t =
        state.tasks.find(
            x => String(x.id) === String(id)
        );


    try {

        await api('/api/task/' + id, {

            method: 'PATCH',

            body: JSON.stringify({

                done: !t.done,

                completed_at:
                    !t.done
                        ? new Date().toISOString()
                        : null

            })

        });


        await load();

        toast(
            t.done
                ? 'Task reopened'
                : 'Task completed ✦'
        );


    } catch (e) {

        toast('Cloud sync unavailable');
    }
}


/* ================================
   DELETE TASK
================================ */

async function deleteTask(id) {

    try {

        await api('/api/task/' + id, {

            method: 'DELETE'

        });

        await load();

        toast('Task removed');


    } catch (e) {

        toast('Cloud sync unavailable');
    }
}


/* ================================
   SAVE TASK
================================ */

$('saveTask').onclick = async () => {

    const input = $('newTask');

    const name = input.value.trim();


    if (!name) {

        return toast('Give the task a name first.');
    }


    try {

        await api('/api/task', {

            method: 'POST',

            body: JSON.stringify({

                title: name,

                priority: $('taskPriority').value,

                done: false

            })

        });


        input.value = '';

        await load();

        toast('Task added to your cloud plan ✦');


    } catch (e) {

        toast('Connect Supabase to save tasks');
    }
};


/* ================================
   ADD TASK BUTTON
================================ */

$('addTaskBtn').onclick = () => {

    $('newTask').focus();

    document
        .querySelector('[data-section="planner"]')
        .click();
};


/* ================================
   MOOD HISTORY
================================ */

function renderHistory() {

    const box = $('moodHistory');


    if (!state.moods.length) {

        box.innerHTML =
            '<div class="empty">Start logging moods to see your pattern.</div>';

        return;
    }


    const counts = {};


    state.moods.forEach(m => {

        counts[m.mood] =
            (counts[m.mood] || 0) + 1;

    });


    const max =
        Math.max(...Object.values(counts));


    box.innerHTML =
        Object.entries(counts)
            .map(
                ([m, n]) =>
                    `
                    <div
                        class="bar"
                        style="height:${40 + n / max * 130}px">

                        <span>
                            ${esc(m)}
                        </span>

                    </div>
                    `
            )
            .join('');


    $('insightText').textContent =
        `Your recent signals show ${state.moods[0].mood.toLowerCase()} as your latest state. Neura can use this history to shape future plans.`;
}


/* ================================
   NAVIGATION
================================ */

function nav() {

    document
        .querySelectorAll('.nav-item')
        .forEach(b => {

            b.onclick = () => {

                document
                    .querySelectorAll('.nav-item')
                    .forEach(x =>
                        x.classList.remove('active')
                    );


                document
                    .querySelectorAll('.section')
                    .forEach(x =>
                        x.classList.remove('active')
                    );


                b.classList.add('active');

                $(b.dataset.section)
                    .classList.add('active');


                $('pageTitle').textContent =
                    {
                        overview: 'Adaptive home',
                        planner: 'Your planner',
                        focus: 'Focus lab',
                        insights: 'Mood insights',
                        tips: 'Smart library'
                    }[b.dataset.section];

            };

        });
}

nav();


/* ================================
   FOCUS TIMER
================================ */

let remaining = 1500;

let interval = null;


function draw() {

    const m =
        String(
            Math.floor(remaining / 60)
        ).padStart(2, '0');


    const s =
        String(
            remaining % 60
        ).padStart(2, '0');


    $('timer').textContent =
        m + ':' + s;

    $('timerLarge').textContent =
        m + ':' + s;
}


async function start() {

    if (interval) {

        clearInterval(interval);

        interval = null;

        $('startTimer').textContent =
            'Resume focus';

        $('startTimerLarge').textContent =
            'Resume session';

        return;
    }


    $('startTimer').textContent =
        'Pause';

    $('startTimerLarge').textContent =
        'Pause session';


    $('timerStatus').textContent =
        'Focus mode — one outcome at a time.';

    $('focusMessage').textContent =
        'Deep work in progress…';


    interval =
        setInterval(
            async () => {

                remaining--;

                draw();


                if (remaining <= 0) {

                    clearInterval(interval);

                    interval = null;

                    sessions++;


                    await api('/api/focus', {

                        method: 'POST',

                        body: JSON.stringify({

                            duration_minutes: 25,

                            mood: selectedMood

                        })

                    }).catch(() => {});


                    remaining = 1500;

                    draw();

                    updateStats();

                    toast(
                        'Focus session completed ✦'
                    );
                }

            },
            1000
        );
}


$('startTimer').onclick = start;

$('startTimerLarge').onclick = start;


$('resetTimer').onclick = () => {

    clearInterval(interval);

    interval = null;

    remaining = 1500;

    draw();

    $('startTimer').textContent =
        'Start focus';

    $('startTimerLarge').textContent =
        'Start 25 min session';
};


draw();


/* ================================
   NEURA COPILOT
================================ */

$('chatOpen').onclick = () =>
    $('chat').classList.add('open');


$('chatClose').onclick = () =>
    $('chat').classList.remove('open');


async function send() {

    const input = $('chatInput');

    const msg = input.value.trim();


    if (!msg) return;


    const box = $('chatMessages');


    box.innerHTML +=
        `<div class="user-msg">${esc(msg)}</div>`;


    input.value = '';

    box.scrollTop = box.scrollHeight;


    try {

        const d = await api('/api/chat', {

            method: 'POST',

            body: JSON.stringify({

                message: msg

            })

        });


        box.innerHTML +=
            `<div class="bot">${esc(d.reply)}</div>`;


    } catch (e) {

        box.innerHTML +=
            `<div class="bot">I’m offline from the AI provider. Add your AI keys in .env to activate the copilot.</div>`;
    }


    box.scrollTop = box.scrollHeight;
}


$('chatSend').onclick = send;


$('chatInput').addEventListener(
    'keydown',
    e => {

        if (e.key === 'Enter') {

            send();

        }

    }
);


/* ================================
   INITIAL LOAD
================================ */

load();