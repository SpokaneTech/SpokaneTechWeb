// Function to generate random position
function getRandomPosition(existingPositions, iconSize) {
    var screenWidth = window.innerWidth;
    var screenHeight = window.innerHeight;
    var randomX, randomY;
    var overlap;
  
    do {
      randomX = Math.floor(Math.random() * (screenWidth - iconSize - 100));
      randomY = Math.floor(Math.random() * (screenHeight - iconSize - 100));
      overlap = existingPositions.some((pos) => {
        return (
          randomX < pos.x + iconSize &&
          randomX + iconSize > pos.x &&
          randomY < pos.y + iconSize &&
          randomY + iconSize > pos.y
        );
      });
    } while (overlap);
  
    return { x: randomX, y: randomY };
  }
  
  // Function to create random icons
  function createRandomIcons(numIcons) {
    var iconsContainer = document.createElement("div");
    iconsContainer.classList.add("icons-container");
    var iconClasses = [
      '<i class="fa-brands fa-python"></i>',
      '<i class="fa-brands fa-golang"></i>',
      '<i class="fa-brands fa-rust"></i>',
      '<i class="fa-brands fa-microsoft"></i>',
      '<i class="fa-solid fa-microchip"></i>',
      '<i class="fa-brands fa-docker"></i>',
      '<i class="fa-brands fa-github"></i>',
      '<i class="fa-brands fa-git"></i>',
      '<i class="fa-solid fa-code-branch"></i>',
      '<i class="fa-solid fa-database"></i>',
      '<i class="fa-solid fa-server"></i>',
      '<i class="fa-brands fa-discord"></i>',
      '<i class="fa-solid fa-code"></i>',
      '<i class="fa-solid fa-network-wired"></i>',
      '<i class="fa-brands fa-linkedin"></i>',
      '<i class="fa-brands fa-aws"></i>',
      '<i class="fa-brands fa-google"></i>',
      '<i class="fa-brands fa-google-play"></i>',
      '<i class="fa-brands fa-app-store-ios"></i>',
      '<i class="fa-brands fa-html5"></i>',
      '<i class="fa-brands fa-css3-alt"></i>',
      '<i class="fa-brands fa-js"></i>',
      '<i class="fa-brands fa-codepen"></i>',
      '<i class="fa-solid fa-terminal"></i>',
      '<i class="fa-brands fa-stack-overflow"></i>',
      '<i class="fa-solid fa-layer-group"></i>',
      '<i class="fa-solid fa-dharmachakra"></i>',
      '<i class="fa-brands fa-python"></i>',
      '<i class="fa-brands fa-golang"></i>',
      '<i class="fa-brands fa-rust"></i>',
    ];
    var usedIcons = [];
    var existingPositions = [];
    var iconSize = 32 + 100; // Approximate size of the icon in pixels
  
    if (numIcons > iconClasses.length) {
      numIcons = iconClasses.length; // Ensure we don't try to use more icons than available
    }
  
    for (var i = 0; i < numIcons; i++) {
      var randomIconClass;
      do {
        randomIconClass =
          iconClasses[Math.floor(Math.random() * iconClasses.length)];
      } while (usedIcons.includes(randomIconClass));
      usedIcons.push(randomIconClass);
  
      var icon = document.createElement("div");
      icon.classList.add("icon");
      icon.innerHTML = randomIconClass;
      var randomPosition = getRandomPosition(existingPositions, iconSize);
      existingPositions.push(randomPosition);
      icon.style.top = randomPosition.y + "px";
      icon.style.left = randomPosition.x + "px";
      icon.style.animation =
        "glow " + (Math.random() * 20 + 10) + "s infinite alternate"; // Random duration for glow animation
      iconsContainer.appendChild(icon);
    }
    document.body.appendChild(iconsContainer);
  }
  
  function getIconCount() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const minSize = Math.min(width, height);
    return Math.floor(minSize / 100) + 1;
  }


  // Create random icons
  document.addEventListener("DOMContentLoaded", () => {
    icon_count = getIconCount();
    createRandomIcons(icon_count);
  });
  