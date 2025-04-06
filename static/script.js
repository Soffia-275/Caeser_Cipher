document.getElementById('decrypt-btn').addEventListener('click', async () => {
    const cipherText = document.getElementById('cipher-text').value.trim();

    if (!cipherText) {
        alert('Please enter cipher text.');
        return;
    }

    try {
        const response = await fetch('/decrypt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cipher_text: cipherText })
        });

        const data = await response.json();
        if (response.ok) {
            document.querySelector('#decrypted-text span').textContent = data.decrypted_text;
            document.querySelector('#predicted-shift span').textContent = data.predicted_shift;
        } else {
            alert(data.error || 'An error occurred.');
        }
    } catch (error) {
        alert('Failed to decrypt text.');
    }
});
