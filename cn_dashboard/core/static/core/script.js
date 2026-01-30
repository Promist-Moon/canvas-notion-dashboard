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

function handleAction(type) {
    if (type === 'create') {
        alert("Initializing Notion Database structure...");
        // Add your Django/API call logic here
    } else if (type === 'import') {
        const card = event.currentTarget;
        card.classList.add('loading');
        card.querySelector('p').innerText = "Syncing with Canvas...";
        
        // Simulate a sync process
        setTimeout(() => {
            card.classList.remove('loading');
            card.querySelector('p').innerText = "Sync complete! Check Notion.";
            card.querySelector('.card-icon').innerText = "✅";
        }, 3000);
    }
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