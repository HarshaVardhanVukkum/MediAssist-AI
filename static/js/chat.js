document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");
  const messages = document.getElementById("chatMessages");
  if (!form || !input || !messages) return;

  function addMessage(text, who) {
    const row = document.createElement("div");
    row.className = `message ${who === "user" ? "user-message" : "assistant-message"}`;
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = who === "user" ? "You" : "✧";
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    const p = document.createElement("p");
    p.textContent = text;
    bubble.appendChild(p);
    row.append(avatar, bubble);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
    return row;
  }

  async function sendMessage(text) {
    if (!text.trim()) return;
    addMessage(text, "user");
    input.value = "";
    input.disabled = true;
    const waiting = addMessage("Thinking…", "assistant");
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: text})
      });
      const data = await response.json();
      waiting.querySelector(".message-bubble p").textContent =
        data.reply || "Sorry, I couldn't answer that. Please try again.";
    } catch (_error) {
      waiting.querySelector(".message-bubble p").textContent =
        "I couldn't reach the assistant. Please check that the Flask server is running.";
    } finally {
      input.disabled = false;
      input.focus();
      messages.scrollTop = messages.scrollHeight;
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(input.value);
  });
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => sendMessage(button.dataset.prompt));
  });
});
