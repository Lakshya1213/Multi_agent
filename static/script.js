const tabs = document.querySelectorAll(".tab");
const pasteTab = document.getElementById("pasteTab");
const uploadTab = document.getElementById("uploadTab");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const analyzeBtn = document.getElementById("analyzeBtn");
const results = document.getElementById("results");
const newAnalysisBtn = document.getElementById("newAnalysisBtn");
const transcriptInput = document.getElementById("transcriptInput");

let selectedFile = null;

const sampleExamples = [
  {
    speaker: "advisor",
    text: "Good afternoon, this is Mahesh calling from Fin Ideas. I wanted to speak with Joicy, sir."
  },
  {
    speaker: "advisor",
    text: "You are interested in our Fin Raster strategy, where we provide hedging solutions for existing mutual fund and equity portfolios. Is this a good time to discuss?"
  },
  {
    speaker: "customer",
    text: "Yes. I saw some YouTube videos and wanted to know the minimum amount needed for investment."
  },
  {
    speaker: "advisor",
    text: "We run two kinds of models. In the advisory model, we create a new portfolio using Nifty ETF and Nifty futures, and hedge it with December put options of the Nifty."
  },
  {
    speaker: "advisor",
    text: "The minimum investment is one lot of Nifty, which comes to around 16 lakh rupees at present."
  },
  {
    speaker: "customer",
    text: "Okay."
  },
  {
    speaker: "advisor",
    text: "Out of the 16 lakh, around 10 percent, that is 1.6 lakh, is used for futures and options for the full year."
  },
  {
    speaker: "advisor",
    text: "Using this 1.6 lakh, we create a position equivalent to 16 lakh in Nifty, which is downside protected."
  },
  {
    speaker: "advisor",
    text: "To recover this cost, the remaining funds are parked in fixed income instruments ranging from 7.5% to 14-15%. You get around 9-10% back from there."
  },
  {
    speaker: "advisor",
    text: "The maximum risk in this scenario is less than 2%. Even if the market goes down by 50%, you are not expected to lose more than 2% on the entire 16 lakh investment."
  },
  {
    speaker: "customer",
    text: "So 16 lakh is the minimum amount needed for an investor, right?"
  },
  {
    speaker: "advisor",
    text: "Yes. If you can create a 16 lakh position using just 10 percent funds, you may manage the remaining 90 percent yourself, but only if you can generate more than 9 percent annual returns."
  },
  {
    speaker: "advisor",
    text: "If you are not sure about generating that return yourself, it is better to invest the full 16 lakh and protect the downside."
  },
  {
    speaker: "customer",
    text: "You said from 16 lakh, 10 percent goes into futures and options, right?"
  },
  {
    speaker: "advisor",
    text: "Yes. We buy one lot of futures and one lot of put options for the year."
  },
  {
    speaker: "customer",
    text: "And how much do you invest in ETF?"
  },
  {
    speaker: "advisor",
    text: "In one lot, we do not buy the Nifty ETF. You can buy Nifty ETF for 4-5 lakh also, but protection is not available for 4 lakh. Protection is available directly for 16 lakh."
  },
  {
    speaker: "advisor",
    text: "The objective of creating one lot, or 16 lakh exposure, is met using Nifty futures. One lot of Nifty futures gives equivalent market exposure."
  }
];

const sampleButtons = document.querySelectorAll(".sample-btn");

sampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const index = Number(button.dataset.index);
    const example = sampleExamples[index];

    document.getElementById("speakerSelect").value = formatSpeakerValue(example.speaker);
    transcriptInput.value = example.text;

    tabs.forEach((btn) => btn.classList.remove("active"));
    document.querySelector('[data-tab="paste"]').classList.add("active");

    pasteTab.classList.add("active");
    uploadTab.classList.remove("active");
  });
});

// ------------------------------
// Tab Switching
// ------------------------------
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

// ------------------------------
// File Upload UI
// ------------------------------
fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    selectedFile = fileInput.files[0];
    fileName.textContent = `Selected file: ${selectedFile.name}`;
  } else {
    selectedFile = null;
    fileName.textContent = "No file selected";
  }
});

// ------------------------------
// Analyze Conversation
// ------------------------------
analyzeBtn.addEventListener("click", async () => {
  const speaker = document.getElementById("speakerSelect").value;
  const transcript = transcriptInput.value;
  const isUploadTab = uploadTab.classList.contains("active");

  analyzeBtn.textContent = "Analyzing...";
  analyzeBtn.disabled = true;

  try {
    let response;

    if (isUploadTab) {
      if (!selectedFile) {
        alert("Please upload a file first.");
        analyzeBtn.textContent = "Analyze Conversation";
        analyzeBtn.disabled = false;
        return;
      }

      const formData = new FormData();
      formData.append("file", selectedFile);

      response = await fetch("/upload", {
        method: "POST",
        body: formData
      });

    } else {
      if (!transcript.trim()) {
        alert("Please enter transcript first.");
        analyzeBtn.textContent = "Analyze Conversation";
        analyzeBtn.disabled = false;
        return;
      }

      response = await fetch("/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          speaker: speaker.toLowerCase(),
          transcript: transcript
        })
      });
    }

    if (!response.ok) {
      throw new Error("API request failed");
    }

    const result = await response.json();

    if (result.error) {
      alert(result.error);
      analyzeBtn.textContent = "Analyze Conversation";
      analyzeBtn.disabled = false;
      return;
    }

    console.log("Backend Result:", result);

    updateAgentOutput(result);
    updateChecklist(result);
    updateConversationHistory(result.conversation_window);
    updateOutputAnalysis(result);
    updateSummary(result);

    results.classList.remove("hidden");

    results.scrollIntoView({
      behavior: "smooth"
    });

  } catch (error) {
    console.error("Error:", error);
    alert("Backend error. Check FastAPI terminal.");
  }

  analyzeBtn.textContent = "Analyze Conversation";
  analyzeBtn.disabled = false;
});

// ------------------------------
// Update Agent Output
// ------------------------------
function updateAgentOutput(result) {
  document.getElementById("currentStage").textContent =
    result.active_stage || "Unknown";

  const confidence = result.stage_detection?.confidence || 0;

  document.getElementById("confidenceScore").textContent =
    Math.round(confidence * 100) + "%";

  document.getElementById("stageCompleted").textContent =
    result.stage_completed ? "Yes" : "No";

  const progress = result.checklist?.completion_percent || 0;

  document.getElementById("checklistProgress").textContent =
    progress + "%";

  document.getElementById("progressFill").style.width =
    progress + "%";

  document.getElementById("nextQuestion").textContent =
    result.next_best_question || "No question generated.";
}

// ------------------------------
// Update Checklist
// ------------------------------
function updateChecklist(result) {
  const coveredItems = result.checklist?.covered_items || [];
  const missingItems = result.checklist?.missing_items || [];

  updateList("coveredItems", coveredItems);
  updateList("missingItems", missingItems);
}

function updateList(elementId, items) {
  const list = document.getElementById(elementId);
  list.innerHTML = "";

  if (!items || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = "None";
    list.appendChild(li);
    return;
  }

  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = formatText(item);
    list.appendChild(li);
  });
}

// ------------------------------
// Conversation History
// ------------------------------
function updateConversationHistory(conversationWindow) {
  const chatBox = document.getElementById("conversationHistory");
  chatBox.innerHTML = "";

  if (!conversationWindow || conversationWindow.length === 0) {
    chatBox.innerHTML = "<p>No conversation history yet.</p>";
    return;
  }

  conversationWindow.forEach((msg) => {
    const div = document.createElement("div");

    const speakerClass = msg.speaker === "advisor" ? "advisor" : "customer";

    div.className = `bubble ${speakerClass}`;
    div.innerHTML = `<strong>${formatText(msg.speaker)}:</strong> ${msg.text}`;

    chatBox.appendChild(div);
  });
}

// ------------------------------
// Output Analysis
// ------------------------------
function updateOutputAnalysis(result) {
  const stageReason = result.stage_detection?.reason || "No reason available.";
  const checklistReason = result.checklist?.reason || "No checklist reason available.";
  const missingItems = result.checklist?.missing_items || [];

  const whyStage = document.getElementById("whyStage");
  const whyChecklist = document.getElementById("whyChecklist");
  const whatMissing = document.getElementById("whatMissing");
  const advisorAction = document.getElementById("advisorAction");

  if (whyStage) {
    whyStage.textContent = stageReason;
  }

  if (whyChecklist) {
    whyChecklist.textContent = checklistReason;
  }

  if (whatMissing) {
    if (missingItems.length > 0) {
      whatMissing.textContent =
        "Things still to cover: " + missingItems.map(formatText).join(", ");
    } else {
      whatMissing.textContent = "No missing checklist items.";
    }
  }

  if (advisorAction) {
    advisorAction.textContent =
      result.next_best_question || "Continue the conversation naturally.";
  }
}

// ------------------------------
// Summary
// ------------------------------
function updateSummary(result) {
  const summaryIntent = document.getElementById("summaryIntent");
  const summaryConcern = document.getElementById("summaryConcern");
  const summaryNextStep = document.getElementById("summaryNextStep");

  if (summaryIntent) {
    summaryIntent.textContent =
      `Current conversation is in ${result.active_stage || "Unknown"} stage.`;
  }

  if (summaryConcern) {
    const missingItems = result.checklist?.missing_items || [];

    summaryConcern.textContent =
      missingItems.length > 0
        ? missingItems.map(formatText).join(", ")
        : "No major missing context.";
  }

  if (summaryNextStep) {
    summaryNextStep.textContent =
      result.next_best_question || "Continue conversation.";
  }
}

// ------------------------------
// New Analysis / Reset
// ------------------------------
newAnalysisBtn.addEventListener("click", async () => {
  transcriptInput.value = "";
  fileInput.value = "";
  selectedFile = null;
  fileName.textContent = "No file selected";
  results.classList.add("hidden");

  try {
    await fetch("/reset", {
      method: "POST"
    });
  } catch (error) {
    console.error("Reset error:", error);
  }

  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
});

// ------------------------------
// Helpers
// ------------------------------
function formatText(text) {
  if (!text) return "";

  return text
    .toString()
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatSpeakerValue(speaker) {
  if (!speaker) return "Customer";

  const lower = speaker.toLowerCase();

  if (lower === "advisor") return "Advisor";
  if (lower === "customer") return "Customer";

  return "Customer";
}