document.addEventListener("DOMContentLoaded", () => {

  // Result Page Chart
  const resultChart = document.getElementById("resultChart");
  if (resultChart) {
    const fakeProb = parseFloat(resultChart.dataset.fakeprob);
    new Chart(resultChart, {
      type: "doughnut",
      data: {
        labels: ["Fake Probability", "Real Confidence"],
        datasets: [{
          data: [fakeProb, 1 - fakeProb],
          backgroundColor: ["#ff4d6d", "#28a745"],
          borderWidth: 2
        }]
      },
      options: {
        plugins: { legend: { position: "bottom" } },
        cutout: "70%",
        animation: { animateScale: true }
      }
    });
  }

  // Dashboard Charts
  const dataDiv = document.getElementById("data");
  if (dataDiv) {
    const filenames = JSON.parse(dataDiv.dataset.filenames);
    const ai_scores = JSON.parse(dataDiv.dataset.aiscores);
    const authenticity = JSON.parse(dataDiv.dataset.authscores);
    const blockchain = JSON.parse(dataDiv.dataset.blockchain);
    const real_count = parseInt(dataDiv.dataset.real);
    const fake_count = parseInt(dataDiv.dataset.fake);

    // 1️⃣ Bar Chart
    new Chart(document.getElementById("barChart"), {
      type: "bar",
      data: {
        labels: filenames,
        datasets: [{ label: "Fake Probability", data: ai_scores, backgroundColor: "#f44336" }]
      },
      options: { responsive: true, scales: { y: { beginAtZero: true, max: 1 } } }
    });

    // 2️⃣ Line Chart
    new Chart(document.getElementById("lineChart"), {
      type: "line",
      data: {
        labels: filenames,
        datasets: [{ label: "Authenticity Score", data: authenticity, borderColor: "#4caf50", tension: 0.3 }]
      },
      options: { responsive: true }
    });

    // 3️⃣ Pie Chart
    new Chart(document.getElementById("pieChart"), {
      type: "pie",
      data: { labels: ["Real", "Fake"], datasets: [{ data: [real_count, fake_count], backgroundColor: ["#4caf50", "#f44336"] }] }
    });

    // 4️⃣ Blockchain Chart
    new Chart(document.getElementById("barChart2"), {
      type: "bar",
      data: {
        labels: filenames,
        datasets: [{ label: "Blockchain Verification", data: blockchain.map(b => b === "Verified" ? 1 : 0), backgroundColor: "#2196f3" }]
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
            max: 1,
            ticks: { callback: v => v === 1 ? "Verified" : "Not Verified" }
          }
        }
      }
    });
  }
});
