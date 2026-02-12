// document.addEventListener('DOMContentLoaded', () => {
//     const fetchButton = document.querySelector('#fetch-button');
//     const videoUrlInput = document.querySelector('input[name="video_url"]');

//     fetchButton.addEventListener('click', async () => {
//         const videoUrl = videoUrlInput.value;
//         if (!videoUrl) return;
//         // launch wheel

//     });
// });

function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return "";
  const total = Math.floor(seconds);
  const hrs = Math.floor(total / 3600);
  const mins = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return hrs > 0 ? `${hrs}:${pad(mins)}:${pad(secs)}s` : `${mins}:${pad(secs)}s`;
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes < 0) return "";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  return `${value.toFixed(value < 10 && i > 0 ? 1 : 0)} ${units[i]}`;
}

function formatDate(value) {
    if (!/^\d{8}$/.test(value)) return "";
    const year = value.slice(0, 4);
    const month = value.slice(4, 6);
    const day = value.slice(6, 8);
    const date = new Date(`${year}-${month}-${day}T00:00:00`);
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
  }

async function pollFetchStatus() {
  const element = document.getElementById("fetch-status");
  if (!element) return;
  const url = element.dataset.url;
  if (!url) return;

  const response = await fetch(url, { credentials: "same-origin" });
  const data = await response.json();
  if (data.status === "success" && data.data) {
    // Update only the metadata section
    const meta = document.getElementById("video-metadata");
    if (meta) meta.classList.remove("hidden");
    const loading = document.getElementById("fetch-loading");
    if (loading) loading.classList.add("hidden");
    document.getElementById("video-thumbnail").src = data.data.thumbnail || "";
    document.getElementById("video-title").textContent = data.data.title || "Unknown Title";
    document.getElementById("video-duration").textContent = formatDuration(data.data.duration);
    document.getElementById("video-quality").textContent = data.data.height ? `${data.data.height}p` : "";
    document.getElementById("video-channel").textContent = data.data.uploader || "Unknown Channel";
    document.getElementById("video-size").textContent = formatBytes(
      data.data.filesize || data.data.filesize_approx
    );
    document.getElementById("video-date").textContent = "Uploaded on " + formatDate(data.data.upload_date) || "Unknown Date";
    return;
  }
  if (data.status === "error") {
    const meta = document.getElementById("video-metadata");
    if (meta) meta.classList.remove("hidden");
    const loading = document.getElementById("fetch-loading");
    if (loading) loading.classList.add("hidden");
    const errorText = document.getElementById("video-error");
    if (errorText) {
      errorText.textContent = data.message || "Failed to fetch metadata.";
    }
    return;
  }
  if (data.status === "none") {
    const loading = document.getElementById("fetch-loading");
    if (loading) loading.classList.add("hidden");
    return;
  }
  // Keep polling while running/pending
  if (data.status === "pending") {
    const loading = document.getElementById("fetch-loading");
    if (loading) loading.classList.remove("hidden");
    setTimeout(pollFetchStatus, 1500);
  }
}

pollFetchStatus();
