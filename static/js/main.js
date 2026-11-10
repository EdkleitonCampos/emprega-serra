document.addEventListener("DOMContentLoaded", () => {
    const menuToggle = document.getElementById("menuToggle");
    const mainNav = document.getElementById("mainNav");

    if (menuToggle && mainNav) {
        menuToggle.addEventListener("click", () => {
            const isOpen = mainNav.classList.toggle("open");
            menuToggle.setAttribute("aria-expanded", String(isOpen));
        });

        mainNav.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => {
                mainNav.classList.remove("open");
                menuToggle.setAttribute("aria-expanded", "false");
            });
        });
    }

    // Filtro demonstrativo das vagas que aparecem na página inicial.
    const searchForm = document.getElementById("jobSearch");
    const searchInput = document.getElementById("searchInput");
    const locationInput = document.getElementById("locationInput");
    const jobCards = Array.from(document.querySelectorAll(".job-card"));
    const emptyState = document.getElementById("emptyState");

    if (searchForm) {
        searchForm.addEventListener("submit", (event) => {
            event.preventDefault();
            const term = (searchInput.value + " " + locationInput.value)
                .trim()
                .toLocaleLowerCase("pt-BR");

            let visibleCount = 0;
            jobCards.forEach((card) => {
                const content = card.dataset.search || "";
                // Como os exemplos são todos da cidade informada, a busca considera
                // o texto digitado no campo de cargo/área.
                const keyword = searchInput.value.trim().toLocaleLowerCase("pt-BR");
                const matches = !keyword || content.includes(keyword);
                card.hidden = !matches;
                if (matches) visibleCount += 1;
            });

            if (emptyState) emptyState.hidden = visibleCount !== 0;
            document.getElementById("vagas").scrollIntoView({ behavior: "smooth" });
        });
    }
});
