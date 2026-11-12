document.addEventListener("DOMContentLoaded", () => {
    const pauseConfirmDialog = document.getElementById("pauseConfirmDialog");
    const pauseTypeDialog = document.getElementById("pauseTypeDialog");
    const pauseScheduleDialog = document.getElementById("pauseScheduleDialog");
    const finalizeConfirmDialog = document.getElementById("finalizeConfirmDialog");
    const pauseScheduleForm = document.getElementById("pauseScheduleForm");
    const pauseUntilInput = document.getElementById("pauseUntil");
    let pendingPauseUrl = "";
    let pendingFinalizeForm = null;

    const setDialogVacancyTitle = (dialog, title) => {
        const titleElement = dialog?.querySelector("[data-dialog-vacancy-title]");
        if (titleElement) titleElement.textContent = title;
    };

    const openFinalizeDialog = (form) => {
        pendingFinalizeForm = form;
        const statusSelect = form.querySelector("select[name='status']");
        const isCancellation = statusSelect instanceof HTMLSelectElement
            && statusSelect.value === "cancelada";
        const title = finalizeConfirmDialog?.querySelector("#finalizeConfirmTitle");
        const message = finalizeConfirmDialog?.querySelector("[data-finalize-message]");
        const confirmButton = finalizeConfirmDialog?.querySelector("[data-confirm-finalize]");
        if (title) title.textContent = isCancellation ? "Cancelar vaga?" : "Finalizar vaga?";
        if (message) {
            const verb = isCancellation ? "cancelar" : "finalizar";
            message.firstChild.textContent = `Tem certeza que deseja ${verb} `;
        }
        if (confirmButton) {
            confirmButton.textContent = isCancellation ? "Sim, cancelar" : "Sim, finalizar";
        }
        setDialogVacancyTitle(finalizeConfirmDialog, form.dataset.vacancyTitle || "esta vaga");
        if (statusSelect instanceof HTMLSelectElement) {
            statusSelect.dataset.currentStatus = form.dataset.originalStatus || statusSelect.value;
        }
        finalizeConfirmDialog?.showModal();
    };

    document.querySelectorAll("[data-pause-url]").forEach((button) => {
        button.addEventListener("click", () => {
            pendingPauseUrl = button.dataset.pauseUrl;
            setDialogVacancyTitle(
                pauseConfirmDialog,
                button.dataset.vacancyTitle || "esta vaga"
            );
            pauseConfirmDialog?.showModal();
        });
    });

    document.querySelector("[data-confirm-pause]")?.addEventListener("click", () => {
        pauseConfirmDialog?.close();
        pauseTypeDialog?.showModal();
    });

    document.querySelector("[data-pause-indefinitely]")?.addEventListener("click", () => {
        if (!pendingPauseUrl) return;

        const form = document.createElement("form");
        form.method = "POST";
        form.action = pendingPauseUrl;
        const dateField = document.createElement("input");
        dateField.type = "hidden";
        dateField.name = "pausa_ate";
        form.append(dateField);
        document.body.append(form);
        form.submit();
    });

    document.querySelector("[data-schedule-pause]")?.addEventListener("click", () => {
        if (!pendingPauseUrl || !(pauseScheduleForm instanceof HTMLFormElement)) return;

        const now = new Date();
        now.setDate(now.getDate() + 1);
        const localDate = [
            now.getFullYear(),
            String(now.getMonth() + 1).padStart(2, "0"),
            String(now.getDate()).padStart(2, "0")
        ].join("-");
        if (pauseUntilInput instanceof HTMLInputElement) pauseUntilInput.min = localDate;
        pauseScheduleForm.action = pendingPauseUrl;
        pauseTypeDialog?.close();
        pauseScheduleDialog?.showModal();
    });

    document.querySelectorAll("[data-close-dialog]").forEach((button) => {
        button.addEventListener("click", () => {
            button.closest("dialog")?.close();
        });
    });

    document.querySelectorAll("[data-finalize-form]").forEach((form) => {
        if (!(form instanceof HTMLFormElement)) return;
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            openFinalizeDialog(form);
        });
    });

    document.querySelectorAll("[data-edit-vacancy-form]").forEach((form) => {
        if (!(form instanceof HTMLFormElement)) return;
        const select = form.querySelector("select[name='status']");
        if (!(select instanceof HTMLSelectElement)) return;
        select.dataset.currentStatus = form.dataset.originalStatus || select.value;
        form.addEventListener("submit", (event) => {
            if (select.value !== select.dataset.currentStatus
                && ["finalizada", "cancelada"].includes(select.value)) {
                event.preventDefault();
                openFinalizeDialog(form);
            }
        });
    });

    document.querySelector("[data-confirm-finalize]")?.addEventListener("click", () => {
        const form = pendingFinalizeForm;
        finalizeConfirmDialog?.close();
        pendingFinalizeForm = null;
        const confirmButton = finalizeConfirmDialog?.querySelector("[data-confirm-finalize]");
        if (confirmButton) confirmButton.textContent = "Sim, finalizar";
        if (form instanceof HTMLFormElement) form.submit();
    });

    finalizeConfirmDialog?.addEventListener("close", () => {
        if (pendingFinalizeForm instanceof HTMLFormElement) {
            const select = pendingFinalizeForm.querySelector("select[name='status']");
            if (select instanceof HTMLSelectElement) {
                select.value = select.dataset.currentStatus || "aberta";
            }
        }
        pendingFinalizeForm = null;
        const title = finalizeConfirmDialog?.querySelector("#finalizeConfirmTitle");
        const message = finalizeConfirmDialog?.querySelector("[data-finalize-message]");
        if (title) title.textContent = "Finalizar vaga?";
        if (message) message.firstChild.textContent = "Tem certeza que deseja finalizar ";
        const confirmButton = finalizeConfirmDialog?.querySelector("[data-confirm-finalize]");
        if (confirmButton) confirmButton.textContent = "Sim, finalizar";
    });

    const dashboardLinks = Array.from(
        document.querySelectorAll(".dashboard-nav-link[href^='#']")
    );

    if (dashboardLinks.length) {
        const updateDashboardLink = () => {
            const activeHash = window.location.hash || "#visao-geral";
            dashboardLinks.forEach((link) => {
                const isActive = link.getAttribute("href") === activeHash;
                link.classList.toggle("is-active", isActive);
                if (isActive) link.setAttribute("aria-current", "location");
                else link.removeAttribute("aria-current");
            });
        };

        updateDashboardLink();
        window.addEventListener("hashchange", updateDashboardLink);
    }

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

    const accountTypeDialog = document.getElementById("accountTypeDialog");
    const openAccountTypeDialog = document.getElementById("openAccountTypeDialog");

    if (accountTypeDialog && openAccountTypeDialog instanceof HTMLButtonElement) {
        const closeButton = accountTypeDialog.querySelector(".account-type-close");

        openAccountTypeDialog.addEventListener("click", () => {
            accountTypeDialog.showModal();
        });

        closeButton?.addEventListener("click", () => {
            accountTypeDialog.close();
        });

        accountTypeDialog.addEventListener("click", (event) => {
            if (event.target === accountTypeDialog) {
                accountTypeDialog.close();
            }
        });
    }

    document.querySelectorAll(".password-toggle").forEach((toggle) => {
        if (!(toggle instanceof HTMLButtonElement)) return;

        const passwordField = toggle.closest(".password-field");
        const passwordInput = passwordField?.querySelector("input");
        if (!(passwordInput instanceof HTMLInputElement)) return;

        const hidePassword = () => {
            passwordInput.type = "password";
            toggle.setAttribute("aria-label", "Mostrar senha enquanto pressionado");
            toggle.setAttribute("aria-pressed", "false");
        };

        const showPassword = () => {
            passwordInput.type = "text";
            toggle.setAttribute("aria-label", "Senha visível; solte para ocultar");
            toggle.setAttribute("aria-pressed", "true");
        };

        toggle.addEventListener("pointerdown", (event) => {
            event.preventDefault();
            showPassword();
        });
        document.addEventListener("pointerup", hidePassword);
        document.addEventListener("pointercancel", hidePassword);
        toggle.addEventListener("blur", hidePassword);
        toggle.addEventListener("keydown", (event) => {
            if (event.key === " " || event.key === "Enter") {
                event.preventDefault();
                showPassword();
            }
        });
        toggle.addEventListener("keyup", (event) => {
            if (event.key === " " || event.key === "Enter") {
                hidePassword();
            }
        });
    });

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
