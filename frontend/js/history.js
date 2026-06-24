async function loadHistory() {
  const container = document.getElementById('history-container');
  try {
    const res = await fetch('/api/history');
    const entries = await res.json();

    if (!entries.length) {
      container.innerHTML = '<div class="empty-state">Aucun export pour l\'instant. <a href="/">Lance ton premier débit →</a></div>';
      return;
    }

    const rows = entries.map(e => {
      const date = new Date(e.created_at).toLocaleString('fr-FR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
      return `
        <tr>
          <td>${e.project_name || '<span style="color:var(--ink-dim)">—</span>'}</td>
          <td>${date}</td>
          <td style="font-family:var(--mono)">${e.total_panels}</td>
          <td style="font-family:var(--mono)">${e.waste_ratio}%</td>
          <td>
            <a class="dl-link" href="/api/history/${e.id}/recap" download>Récap PDF</a>
            <a class="dl-link" href="/api/history/${e.id}/layout" download>Plans PDF</a>
          </td>
        </tr>`;
    }).join('');

    container.innerHTML = `
      <table class="history-table">
        <thead>
          <tr>
            <th>Projet</th>
            <th>Date</th>
            <th>Panneaux</th>
            <th>Chute</th>
            <th>Fichiers</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`;
  } catch {
    container.innerHTML = '<div class="empty-state">Impossible de charger l\'historique.</div>';
  }
}

loadHistory();
