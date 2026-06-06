const tabs = document.querySelectorAll(".tab");
const pasteTab = document.getElementById("pasteTab");
const uploadTab = document.getElementById("uploadTab");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const analyzeBtn = document.getElementById("analyzeBtn");
const results = document.getElementById("results");
const newAnalysisBtn = document.getElementById("newAnalysisBtn");
const transcriptInput = document.getElementById("transcriptInput");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((btn) => btn.classList.remove("active"));
    tab.classList.add("active");

    const selectedTab = tab.dataset.tab;

    if (selectedTab === "paste") {
      pasteTab.classList.add("active");
      uploadTab.classList.remove("active");
    } else {
      uploadTab.classList.add("active");
      pasteTab.classList.remove("active");
    }
  });
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    fileName.textContent = `Selected file: ${fileInput.files[0].name}`;
  } else {
    fileName.textContent = "No file selected";
  }
});

analyzeBtn.addEventListener("click", () => {
  analyzeBtn.textContent = "Analyzing...";
  analyzeBtn.disabled = true;

  setTimeout(() => {
    results.classList.remove("hidden");

    analyzeBtn.textContent = "Analyze Conversation";
    analyzeBtn.disabled = false;

    results.scrollIntoView({
      behavior: "smooth"
    });
  }, 1000);
});

newAnalysisBtn.addEventListener("click", () => {
  transcriptInput.value = "";
  fileInput.value = "";
  fileName.textContent = "No file selected";
  results.classList.add("hidden");

  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
});