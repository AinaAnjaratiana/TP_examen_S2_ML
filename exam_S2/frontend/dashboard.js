async function chargerTraces() {
    const conteneur = document.getElementById("liste-traces");
    conteneur.innerHTML = "<p>Chargement...</p>";

    try {
        const response = await fetch("/api/observabilite/traces?limite=50");
        const traces = await response.json();

        document.getElementById("resume-traces").textContent =
            traces.length + " trace(s) affichée(s) (les plus récentes en premier)";

        conteneur.innerHTML = "";

        if (traces.length === 0) {
            conteneur.innerHTML = "<p>Aucune trace pour le moment. Analysez un ticket depuis la page Assistant.</p>";
            return;
        }

        traces.forEach((trace) => {
            const section = document.createElement("section");
            section.className = "resultat-trace";
            section.style.background = "white";
            section.style.borderRadius = "10px";
            section.style.padding = "1.2rem 1.5rem";
            section.style.marginBottom = "1rem";
            section.style.boxShadow = "0 1px 4px rgba(0,0,0,0.08)";

            const sortie = trace.sortie || {};

            section.innerHTML = `
                <h3>Ticket #${trace.ticket_id} — ${sortie.categorie ?? "?"} / ${sortie.priorite ?? "?"}</h3>
                <p><strong>Horodatage :</strong> ${trace.horodatage}</p>
                <p><strong>Description :</strong> ${trace.entree?.description ?? ""}</p>
                <p><strong>Décision :</strong> ${sortie.action ?? "?"}
                   &nbsp;|&nbsp; <strong>Confiance :</strong> ${sortie.confiance ?? "?"}
                   &nbsp;|&nbsp; <strong>Validation humaine :</strong> ${sortie.validation_humaine_requise ? "oui" : "non"}</p>
                <p><strong>Latence totale :</strong> ${trace.latence_totale_ms} ms
                   &nbsp;|&nbsp; <strong>Latence RAG :</strong> ${trace.latence_rag_ms} ms</p>

                <table>
                    <thead>
                        <tr><th>Outil</th><th>Statut</th><th>Latence (ms)</th><th>Erreur</th></tr>
                    </thead>
                    <tbody>
                        ${(trace.appels_outils || [])
                            .map(
                                (a) =>
                                    `<tr><td>${a.outil}</td><td>${a.statut}</td><td>${a.latence_ms}</td><td>${a.erreur ?? "-"}</td></tr>`
                            )
                            .join("")}
                    </tbody>
                </table>

                <details>
                    <summary>Détails complets (JSON)</summary>
                    <pre class="details">${JSON.stringify(trace, null, 2)}</pre>
                </details>
            `;

            conteneur.appendChild(section);
        });

    } catch (error) {
        conteneur.innerHTML = "<p>Erreur lors du chargement des traces : " + error.message + "</p>";
    }
}

chargerTraces();
