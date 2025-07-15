document.addEventListener('DOMContentLoaded', () => {
    // --- Initial UI Setup ---
    // Set the initial state for all like buttons when the page loads.
    document.querySelectorAll('.portfolio-card').forEach(card => {
        const carousel = card.querySelector('.carousel');
        
        // Function to update the like button based on the active slide's data
        const updateButtonState = () => {
            const activeSlide = carousel.querySelector('.carousel-item.active');
            if (!activeSlide) return;

            const likes = activeSlide.dataset.likes || 0;
            const isLiked = activeSlide.dataset.isLiked === 'True'; // Jinja renders True/False

            const likeButton = card.querySelector('.like-btn');
            const likeIcon = likeButton.querySelector('i');
            const likesCountSpan = card.querySelector('.likes-count');

            likesCountSpan.textContent = likes;
            if (isLiked) {
                likeIcon.classList.remove('far');
                likeIcon.classList.add('fas', 'text-danger');
            } else {
                likeIcon.classList.remove('fas', 'text-danger');
                likeIcon.classList.add('far');
            }
        };

        // Update the button when the carousel slides
        carousel.addEventListener('slid.bs.carousel', updateButtonState);
        // Set the initial state
        updateButtonState();
    });

    // --- Event Delegation for Clicks ---
    // Listen for clicks on the whole document
    document.body.addEventListener('click', event => {
        // Check if the clicked element is a like button
        const likeButton = event.target.closest('.like-btn');

        // If it's not a like button, do nothing
        if (!likeButton) {
            return;
        }

        // We found a like button, prevent default browser action
        event.preventDefault();
        
        console.log('Like button clicked!'); // DEBUG: Check if click is registered

        const isLoggedIn = document.body.dataset.isLoggedIn === 'true';
            if (!isLoggedIn) {
                const customToast = document.getElementById('customToast');
                const toastBody = customToast.querySelector('.toast-body');
                toastBody.textContent = 'Anda harus login untuk menyukai gambar.';

                // Position the toast near the clicked button
                const rect = likeButton.getBoundingClientRect();
                customToast.style.left = `${rect.left + window.scrollX}px`;
                customToast.style.top = `${rect.top + window.scrollY - customToast.offsetHeight - 10}px`; // 10px above button

                customToast.classList.add('show');
                setTimeout(() => {
                    customToast.classList.remove('show');
                }, 2000); // Hide after 2 seconds
                return;
            }

        // Find the parent card and its active carousel slide
        const card = likeButton.closest('.portfolio-card');
        const activeSlide = card.querySelector('.carousel-item.active');
        
        if (!activeSlide) {
            console.error('Could not find active slide.');
            return;
        }

        const imageId = activeSlide.dataset.imageId;
        console.log(`Found active image ID: ${imageId}`); // DEBUG

        fetch(`/like_image/${imageId}`, { method: 'POST' })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.message || 'Server error'); });
                }
                return response.json();
            })
            .then(data => {
                console.log('Received response from server:', data); // DEBUG
                if (data.success) {
                    // Update the slide's data attributes so state is saved during sliding
                    activeSlide.dataset.likes = data.likes;
                    activeSlide.dataset.isLiked = data.liked ? 'True' : 'False';

                    // Update the UI
                    const likesCountSpan = card.querySelector('.likes-count');
                    const likeIcon = likeButton.querySelector('i');
                    likesCountSpan.textContent = data.likes;
                    if (data.liked) {
                        likeIcon.classList.remove('far');
                        likeIcon.classList.add('fas', 'text-danger');
                        likeIcon.classList.add('like-animation'); // Add animation class
                    } else {
                        likeIcon.classList.remove('fas', 'text-danger');
                        likeIcon.classList.add('far');
                        likeIcon.classList.remove('like-animation'); // Remove animation class
                    }
                } else {
                    alert(data.message || 'An error occurred.');
                }
            })
            .catch(error => {
                console.error('Fetch Error:', error);
                alert('An error occurred: ' + error.message);
            });
    });
});