class ImageGenerator {
    constructor() {
        this.currentPrompt = '';
        this.isGenerating = false;
        this.queue = [];
        this.debounceTimeout = null;
        this.currentImage = document.getElementById('generatedImage');
        this.nextImage = document.getElementById('nextImage');
        this.statusDiv = document.getElementById('status');
        this.setupListeners();
    }

    setupListeners() {
        const textarea = document.getElementById('promptInput');
        textarea.addEventListener('input', (e) => this.handleInput(e.target.value));

        // Setup suggestion chips
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const textarea = document.getElementById('promptInput');
                textarea.value = chip.textContent;
                this.handleInput(chip.textContent);
                textarea.focus();
            });
        });

        // Adjust textarea height automatically
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    handleInput(prompt) {
        this.currentPrompt = prompt.trim();
        
        // Clear previous timeout
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
        }

        // Don't generate for empty prompts
        if (!this.currentPrompt) {
            this.statusDiv.innerHTML = '';
            this.statusDiv.className = 'status';
            return;
        }

        // Set new timeout
        this.debounceTimeout = setTimeout(() => {
            this.queueGeneration(this.currentPrompt);
        }, 800); // Increased to 800ms for better UX
    }

    async queueGeneration(prompt) {
        // Add to queue
        this.queue.push(prompt);
        
        // If not currently generating, start processing queue
        if (!this.isGenerating) {
            this.processQueue();
        }
    }

    async processQueue() {
        if (this.queue.length === 0 || this.isGenerating) {
            return;
        }

        this.isGenerating = true;
        const prompt = this.queue[this.queue.length - 1]; // Get latest prompt
        this.queue = []; // Clear queue

        try {
            this.statusDiv.innerHTML = '<div class="spinner"></div>Creating your imagination...';
            this.statusDiv.className = 'status loading';

            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    prompt: prompt,
                    negative_prompt: "face, ugly, deformed"
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            if (data.images && data.images[0]) {
                const imageData = data.images[0];
                if (imageData.url && imageData.url.startsWith('data:image')) {
                    // Load image in hidden next image element
                    this.nextImage.src = imageData.url;
                    this.nextImage.onload = () => {
                        // Swap images with fade effect
                        this.currentImage.style.opacity = '0';
                        this.nextImage.style.opacity = '1';
                        
                        // After transition, update current image
                        setTimeout(() => {
                            this.currentImage.src = this.nextImage.src;
                            this.currentImage.style.opacity = '1';
                            this.nextImage.style.opacity = '0';
                        }, 300);
                    };
                    
                    this.statusDiv.innerHTML = '✨ Image generated successfully!';
                    this.statusDiv.className = 'status success';
                } else {
                    throw new Error('Invalid image data format received');
                }
            } else {
                throw new Error('No image data received in the response');
            }
        } catch (error) {
            console.error('Error:', error);
            this.statusDiv.innerHTML = `🚫 Error: ${error.message}`;
            this.statusDiv.className = 'status error';
        } finally {
            this.isGenerating = false;
            // Process next item in queue if any
            if (this.queue.length > 0) {
                this.processQueue();
            }
        }
    }
}

// Initialize the generator when the page loads
window.addEventListener('DOMContentLoaded', () => {
    new ImageGenerator();
}); 