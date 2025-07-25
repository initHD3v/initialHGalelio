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
            const postCaption = this.querySelector('.card-text').textContent; // Get caption from the card

            // Update modal title and caption
            document.getElementById('portfolio-modal-title').textContent = postTitle;
            document.getElementById('portfolio-modal-caption').textContent = postCaption;

            // Show spinner while loading
            imageViewerSection.innerHTML = '<div class="spinner-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';

            portfolioViewerModal.show();

            fetch(`/api/posts/${postId}/images`)
                .then(response => response.json())
                .then(data => {
                    // console.log("API Response Data:", data); // Removed for cleaner console
                    imageViewerSection.innerHTML = ''; // Clear spinner
                    if (data.images && data.images.length > 0) {
                        data.images.forEach((filename, index) => {
                            const imgContainer = document.createElement('div');
                            imgContainer.className = 'portfolio-slide'; // Use portfolio-slide class for styling

                            const img = document.createElement('img');
                            img.src = filename; // Use filename directly as it already contains the full static path
                            img.className = 'portfolio-image-display'; // Simpler class for display
                            img.alt = `Image ${index + 1} for ${postTitle}`;
                            img.setAttribute('data-aos', 'fade-up'); // Add AOS animation attribute

                            imgContainer.appendChild(img);
                            imageViewerSection.appendChild(imgContainer);
                        });

                        // Re-initialize AOS to detect new elements and watch the modal's scrollable area
                        AOS.refresh();
                        AOS.init({ 
                            once: false, // Allow animation to happen every time you scroll up or down
                            offset: 50, // Offset (in px) from the original trigger point
                            mirror: true, // Whether elements should animate out while scrolling past them
                            anchorPlacement: 'top-bottom', // Defines which position of the element regarding to window should trigger the animation
                            container: imageViewerSection // Specify the scroll container
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