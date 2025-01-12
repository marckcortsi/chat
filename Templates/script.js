document.addEventListener("DOMContentLoaded", () => {
    const sendButton = document.getElementById("sendButton");
    const photoButton = document.getElementById("photoButton");
    const vibrateButton = document.querySelector(".vibrate-button");
    const fileInput = document.getElementById("fileInput");
    const messageInput = document.getElementById("messageInput");
    const chatMessages = document.getElementById("chatMessages");
    const replyPreview = document.getElementById("replyPreview");
    const replyText = document.getElementById("replyText");
    const cancelReply = document.getElementById("cancelReply");
    const typingIndicator = document.getElementById("typingIndicator");
    const fullscreen = document.getElementById("fullscreen");
    const fullscreenImage = document.getElementById("fullscreenImage");
    const closeFullscreen = document.getElementById("closeFullscreen");
    const chatContainer = document.querySelector(".chat-container");
  
    let typingTimeout;
    let replyMessage = null;
    let isNextMessageReceived = false;
  
    // Generate a random color for messages
    const colorPalette = ["#3949ab", "#26c6da", "#66bb6a", "#ff7043", "#ab47bc", "#ffa726", "#ec407a"];
    function getRandomColor() {
      return colorPalette[Math.floor(Math.random() * colorPalette.length)];
    }
  
    // Add a message to the chat
    function addMessage(content, type, isImage = false) {
      const messageElement = document.createElement("div");
      messageElement.classList.add("message", type);
      messageElement.style.backgroundColor = getRandomColor();
  
      if (isImage) {
        const img = document.createElement("img");
        img.src = content;
        img.addEventListener("click", () => {
          fullscreenImage.src = img.src;
          fullscreen.style.display = "flex";
        });
        messageElement.appendChild(img);
      } else {
        messageElement.textContent = content;
      }
  
      const replyIcon = document.createElement("span");
      replyIcon.classList.add("reply-icon");
      replyIcon.textContent = "↩";
      replyIcon.addEventListener("click", () => {
        replyMessage = isImage ? "una imagen" : content;
        replyText.textContent = `Respondiendo a: ${replyMessage}`;
        replyPreview.style.display = "block";
      });
  
      messageElement.appendChild(replyIcon);
      chatMessages.appendChild(messageElement);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  
    // Cancel reply
    cancelReply.addEventListener("click", () => {
      replyMessage = null;
      replyPreview.style.display = "none";
    });
  
    // Send a message
    sendButton.addEventListener("click", () => {
      const messageText = messageInput.value.trim();
      if (messageText) {
        const messageType = isNextMessageReceived ? "received" : "sent";
        if (replyMessage) {
          addMessage(`Respondiendo a "${replyMessage}": ${messageText}`, messageType);
          replyMessage = null;
          replyPreview.style.display = "none";
        } else {
          addMessage(messageText, messageType);
        }
        isNextMessageReceived = !isNextMessageReceived;
        messageInput.value = "";
      }
    });
  
    // Handle typing indicator
    messageInput.addEventListener("input", () => {
      typingIndicator.style.display = "flex";
      clearTimeout(typingTimeout);
      typingTimeout = setTimeout(() => {
        typingIndicator.style.display = "none";
      }, 2000);
    });
  
    // Handle image selection
    photoButton.addEventListener("click", () => {
      fileInput.click();
    });
  
    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const messageType = isNextMessageReceived ? "received" : "sent";
          addMessage(e.target.result, messageType, true);
          isNextMessageReceived = !isNextMessageReceived;
        };
        reader.readAsDataURL(file);
      }
      fileInput.value = "";
    });
  
    // Close fullscreen image
    closeFullscreen.addEventListener("click", () => {
      fullscreen.style.display = "none";
      fullscreenImage.src = "";
    });
  
    // Handle vibrate button click
    vibrateButton.addEventListener("click", () => {
      chatContainer.classList.add("shake");
      setTimeout(() => {
        chatContainer.classList.remove("shake");
      }, 500); // Remove the animation after 500ms
    });
  });