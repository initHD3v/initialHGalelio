document.addEventListener('DOMContentLoaded', function() {
    const portfolioCards = document.querySelectorAll('.portfolio-clickable');
    const portfolioViewerModalElement = document.getElementById('portfolio-viewer-modal');
    const portfolioViewerModal = new bootstrap.Modal(portfolioViewerModalElement);
    const imageViewerSection = document.getElementById('image-viewer-section');
    const modalCloseButton = portfolioViewerModalElement.querySelector('.btn-close'); // Get the close button

    let lastFocusedElement = null; // Variable to store the last focused element

    // Blur the close button when it's clicked to prevent focus issues
    if (modalCloseButton) {
        modalCloseButton.addEventListener('click', () => {
            modalCloseButton.blur();
        });
    }

    // Close modal on ESC key press
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && portfolioViewerModalElement.classList.contains('show')) {
            portfolioViewerModal.hide();
        }
    });

    // Blur any focused element inside the modal when it starts to hide
    portfolioViewerModalElement.addEventListener('hide.bs.modal', function () {
        if (document.activeElement && portfolioViewerModalElement.contains(document.activeElement)) {
            document.activeElement.blur();
        }
    });

    portfolioCards.forEach(card => {
        card.addEventListener('click', function(event) {
            // Store the currently focused element before opening the modal
            lastFocusedElement = document.activeElement;

            // Prevent carousel slide if clicking on controls/indicators
            if (event.target.closest('.carousel-control-prev') || event.target.closest('.carousel-control-next') || event.target.closest('.carousel-indicators')) {
                return; 
            }
            
            const postId = this.dataset.postId;
            const postTitle = this.querySelector('.card-title').textContent; // Get title from the card

            // Show spinner while loading
            imageViewerSection.innerHTML = '<div class="spinner-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';

            portfolioViewerModal.show();

            fetch(`/api/posts/${postId}/images`)
                .then(response => response.json())
                .then(data => {
                    // console.log("API Response Data:", data); // Removed for cleaner console
                    imageViewerSection.innerHTML = ''; // Clear spinner
                    if (data.images && data.images.length > 0) {
                        // Use a Promise.all to ensure all images are loaded before displaying
                        const imageLoadPromises = data.images.map((filename, index) => {
                            return new Promise((resolve) => {
                                const slideDiv = document.createElement('div');
                                slideDiv.className = 'portfolio-slide';

                                const img = document.createElement('img');
                                img.src = filename; // Use filename directly as it already contains the full static path
                                img.className = 'portfolio-image-display'; // Simpler class for display
                                img.alt = `Image ${index + 1} for ${postTitle}`;
                                img.setAttribute('data-aos', 'fade-up'); // Add AOS animation attribute

                                img.onload = () => {
                                    slideDiv.appendChild(img);
                                    imageViewerSection.appendChild(slideDiv); // Append to imageViewerSection
                                    resolve();
                                };
                                img.onerror = () => {
                                    console.error(`Failed to load image: ${filename}`);
                                    // Append a placeholder or skip this image
                                    slideDiv.innerHTML = '<p class="text-danger">Error loading image</p>';
                                    imageViewerSection.appendChild(slideDiv); // Append to imageViewerSection
                                    resolve();
                                };
                            });
                        });

                        Promise.all(imageLoadPromises).then(() => {
                            // All images loaded, no complex scroll logic needed for simple display
                        });

                    } else {
                        imageViewerSection.innerHTML = '<p class="text-center text-muted">No images found for this post.</p>';
                    }
                })
                .catch(error => {
                    console.error('Error fetching portfolio images:', error);
                    imageViewerSection.innerHTML = '<p class="text-center text-danger">Failed to load images.</p>';
                });
        });
    });

    // Clean up content and ensure body scroll is re-enabled when modal is hidden
    portfolioViewerModalElement.addEventListener('hidden.bs.modal', function () {
        console.log("Modal hidden event triggered. Cleaning up..."); // Debugging log
        imageViewerSection.innerHTML = ''; // Clear content when modal is closed
        // Explicitly ensure body scroll is re-enabled
        document.body.style.overflow = ''; // Reset overflow
        document.documentElement.style.overflow = ''; // Reset overflow for html element
        document.body.classList.remove('modal-open'); // Remove Bootstrap's modal-open class
        document.body.style.pointerEvents = ''; // Ensure pointer events are re-enabled

        // Aggressively remove any lingering modal-backdrop elements
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        // Return focus to the element that had it before the modal opened
        if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
            // Add a small delay to allow Bootstrap's modal closing animation to complete
            setTimeout(() => {
                lastFocusedElement.focus();
                console.log("Focus returned to last focused element.");
            }, 300); // Increased delay to 300ms
        } else {
            document.body.focus(); // Fallback to body if no element was previously focused or focus function is missing
            console.log("Focus returned to body (fallback).");
        }
        console.log("Cleanup complete. Body overflow and modal-open class reset."); // Debugging log
    });
});