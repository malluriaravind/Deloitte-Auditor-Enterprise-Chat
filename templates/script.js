document.getElementById('sendBtn').addEventListener('click', async function() {
    const prompt = document.getElementById('taxPrompt').value;
    if (prompt.trim() === "") {
        alert("Please enter a tax-related question.");
        return;
    }

    const response = await fetch('/api/tax-prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: prompt }),
    });

    const data = await response.json();
    if (data.error) {
        document.getElementById('responseText').innerText = data.error;
    } else {
        document.getElementById('responseText').innerText = data.answer || "No response available.";
    }
});

document.getElementById('cancelBtn').addEventListener('click', function() {
    document.getElementById('taxPrompt').value = "";
    document.getElementById('responseText').innerText = "";
});
