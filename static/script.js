// Nakarat — istemci mantığı.
// Sunucudan gelen kategori/ülke butonları zaten HTML içinde (index.html,
// Jinja ile) render edildi; burada sadece ekranlar arası geçişi ve
// /api/round, /api/guess çağrılarını yönetiyoruz.

const state = {
  category: null,
  categoryLabel: "",
  scope: null,
  country: null,
  roundToken: null,
};

const screens = document.querySelectorAll(".screen");
function showScreen(id) {
  screens.forEach((s) => (s.hidden = s.id !== id));
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => (toast.hidden = true), 3200);
}

/* ---------- Ekran 1 → 2: kategori seçimi ---------- */
document.querySelectorAll(".category-card").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.category = btn.dataset.category;
    state.categoryLabel = btn.dataset.label;
    document.getElementById("scope-title").textContent = `${state.categoryLabel} — yerel mi, evrensel mi?`;
    showScreen("screen-scope");
  });
});

/* ---------- Ekran 2 → 3 ya da doğrudan oyun ---------- */
document.querySelectorAll(".scope-card").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.scope = btn.dataset.scope;
    if (state.scope === "yerel") {
      showScreen("screen-country");
    } else {
      state.country = null;
      startRound();
    }
  });
});

/* ---------- Ekran 3 → oyun ---------- */
document.querySelectorAll(".country-card").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.country = btn.dataset.country;
    startRound();
  });
});

/* ---------- Geri butonları ---------- */
document.querySelectorAll(".back-link").forEach((btn) => {
  btn.addEventListener("click", () => showScreen(btn.dataset.target));
});

/* ---------- Tur başlatma ---------- */
const audio = document.getElementById("audio");
const artwork = document.getElementById("artwork");
const playButton = document.getElementById("play-button");
const iconPlay = document.getElementById("icon-play");
const iconPause = document.getElementById("icon-pause");
const eqBars = document.getElementById("eq-bars");
const guessForm = document.getElementById("guess-form");
const guessBtn = document.getElementById("guess-btn");
const titleInput = document.getElementById("title-guess");
const artistInput = document.getElementById("artist-guess");
const resultPanel = document.getElementById("result-panel");
const resultText = document.getElementById("result-text");
const nextRoundBtn = document.getElementById("next-round-btn");
const scorePill = document.getElementById("score-pill");
const scoreValue = document.getElementById("score-value");
const roundsValue = document.getElementById("rounds-value");

async function startRound() {
  showScreen("screen-game");
  resetGameScreen();

  const params = new URLSearchParams({
    category: state.category,
    scope: state.scope || "evrensel",
  });
  if (state.country) params.set("country", state.country);

  try {
    const res = await fetch(`/api/round?${params.toString()}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Bilinmeyen hata");

    state.roundToken = data.round_token;
    audio.src = data.preview_url;
    artwork.src = data.artwork || "";
    scorePill.hidden = false;
  } catch (err) {
    showToast(err.message || "Şarkı getirilemedi. Tekrar dener misin?");
  }
}

function resetGameScreen() {
  audio.pause();
  audio.currentTime = 0;
  togglePlayIcon(false);
  eqBars.classList.remove("playing");
  titleInput.value = "";
  artistInput.value = "";
  titleInput.disabled = false;
  artistInput.disabled = false;
  guessBtn.disabled = false;
  resultPanel.hidden = true;
  guessForm.hidden = false;
}

/* ---------- Çalma kontrolü ---------- */
function togglePlayIcon(isPlaying) {
  iconPlay.hidden = isPlaying;
  iconPause.hidden = !isPlaying;
}

playButton.addEventListener("click", () => {
  if (audio.paused) {
    audio.play();
  } else {
    audio.pause();
  }
});
audio.addEventListener("play", () => {
  togglePlayIcon(true);
  eqBars.classList.add("playing");
});
audio.addEventListener("pause", () => {
  togglePlayIcon(false);
  eqBars.classList.remove("playing");
});
audio.addEventListener("ended", () => {
  togglePlayIcon(false);
  eqBars.classList.remove("playing");
});

/* ---------- Tahmin gönderme ---------- */
guessForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  guessBtn.disabled = true;

  try {
    const res = await fetch("/api/guess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title_guess: titleInput.value,
        artist_guess: artistInput.value,
        round_token: state.roundToken,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Bilinmeyen hata");

    renderResult(data);
    scoreValue.textContent = data.score;
    roundsValue.textContent = data.rounds_played;
  } catch (err) {
    showToast(err.message || "Tahmin gönderilemedi.");
    guessBtn.disabled = false;
  }
});

function renderResult(data) {
  const titleLine = data.title_correct
    ? `<span class="hit">✓ Şarkı adını bildin</span>`
    : `<span class="miss">✗ Şarkı: ${escapeHtml(data.correct_title)}</span>`;
  const artistLine = data.artist_correct
    ? `<span class="hit">✓ Sanatçıyı bildin</span>`
    : `<span class="miss">✗ Sanatçı: ${escapeHtml(data.correct_artist)}</span>`;

  resultText.innerHTML = `${titleLine}<br>${artistLine}`;
  guessForm.hidden = true;
  resultPanel.hidden = false;
  titleInput.disabled = true;
  artistInput.disabled = true;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

nextRoundBtn.addEventListener("click", startRound);
