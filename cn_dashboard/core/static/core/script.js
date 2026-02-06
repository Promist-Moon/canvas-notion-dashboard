function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) {
        console.warn(`Modal not found: ${id}`);
        return;
    }
    modal.style.display = 'flex';
}
function closeModal(id) {
    const modal = document.getElementById(id);
    if (!modal) {
        console.warn(`Modal not found: ${id}`);
        return;
    }
    modal.style.display = 'none';
}

function handleAction(type, elem) {
    if (type === 'create') {
        const card = document.querySelector('.action-card.highlight-hover');
        // prevent duplicate requests
        if (card && card.dataset.busy === 'true') return;

        const csrftoken = getCookie('csrftoken');

        if (card) {
            card.dataset.busy = 'true';
            card.classList.add('loading');
            card.style.pointerEvents = 'none';
        }

        fetch('/create-database/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({}),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.ok) {
                    if (card) card.querySelector('p').innerText = 'Database created! ID: ' + data.database_id;
                    if (card) card.querySelector('.card-icon').innerText = '✅';
                } else {
                    if (card) card.querySelector('p').innerText = 'Error: ' + (data.error || 'Unknown');
                    if (card) card.classList.add('error');
                }
            })
            .catch((err) => {
                if (card) card.querySelector('p').innerText = 'Network error while creating database.';
            })
            .finally(() => {
                if (card) {
                    card.dataset.busy = 'false';
                    card.classList.remove('loading');
                    card.style.pointerEvents = '';
                }
            });
    } else if (type === 'import') {
        const card = elem || document.querySelector('.action-card.sync-card');
        // prevent duplicate imports
        if (card && card.dataset.busy === 'true') return;

        const infoP = card ? card.querySelector('p') : null;
        if (infoP) infoP.innerText = "Syncing with Canvas...";

        const csrftoken = getCookie('csrftoken');

        if (card) {
            card.dataset.busy = 'true';
            card.classList.add('loading');
            card.style.pointerEvents = 'none';
        }

        fetch('/import-assignments/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({}),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.ok) {
                    if (infoP) infoP.innerText = `Imported ${data.created} new, ${data.updated} updated`;
                    if (card) card.querySelector('.card-icon').innerText = '✅';
                } else {
                    if (infoP) infoP.innerText = 'Error: ' + (data.error || 'Unknown');
                    if (card) card.classList.add('error');
                }
            })
            .catch((err) => {
                if (infoP) infoP.innerText = 'Network error while syncing assignments.';
            })
            .finally(() => {
                if (card) {
                    card.dataset.busy = 'false';
                    card.classList.remove('loading');
                    card.style.pointerEvents = '';
                }
            });
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const propertiesData = document.getElementById("db-properties");
const savedProperties = propertiesData ? JSON.parse(propertiesData.textContent) : [];
const activeProperties = new Set();

window.addEventListener('DOMContentLoaded', () => {
    // Only attempt to loop if savedProperties is an array
    if (Array.isArray(savedProperties)) {
        savedProperties.forEach(prop => {
            const colorMap = {
                'Semester': 'blue',
                'Week': 'orange',
                'URL': 'purple',
                'Status': 'green',
                'Points': 'pink'
            };
            if (colorMap[prop]) {
                toggleProperty(prop, colorMap[prop]);
            }
        });
    }
});

function toggleProperty(name, color) {
    if (activeProperties.has(name)) return;
    activeProperties.add(name);

    const container = document.getElementById('selected-properties-container');
    const pill = document.createElement('span');
    
    // Ensure the class name matches your CSS exactly (e.g., .pill-blue)
    pill.className = `tag pill-${color}`;
    pill.id = `pill-${name}`;
    pill.style.display = 'inline-flex';
    pill.style.alignItems = 'center';
    
    // Use event.stopPropagation() to prevent any weird bubbling
    pill.innerHTML = `${name} <span style="cursor:pointer; margin-left:8px; font-weight:bold;" onclick="event.stopPropagation(); removeProperty('${name}')">×</span>`;
    container.appendChild(pill);

    const hiddenContainer = document.getElementById('hidden-inputs');
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'properties';
    input.value = name;
    input.id = `input-${name}`;
    hiddenContainer.appendChild(input);
}

function removeProperty(name) {
    activeProperties.delete(name);
    document.getElementById(`pill-${name}`).remove();
    document.getElementById(`input-${name}`).remove();
}