document.addEventListener('DOMContentLoaded', () => {
    const isLoggedIn = document.body.dataset.isLoggedIn === 'True';
    const userRole = document.body.dataset.userRole;

    const setupPortfolioCard = (cardElement) => {
        const carousel = cardElement.querySelector('.carousel');
        const likeButton = cardElement.querySelector('.like-btn');
        const likeIcon = cardElement.querySelector('.like-btn i');
        const likesCountSpan = cardElement.querySelector('.likes-count');

        // This is the single source of truth for updating the UI of this card.
        const refreshUI = () => {
            const activeItem = carousel.querySelector('.carousel-item.active');
            if (!activeItem) return;

            const imageId = activeItem.dataset.imageId;
            const currentLikes = activeItem.dataset.likes || 0;
            const isLiked = activeItem.dataset.isLiked === 'True'; // New data attribute

            likesCountSpan.textContent = currentLikes;

            if (isLiked) {
                likeIcon.classList.remove('far');
                likeIcon.classList.add('fas');
            } else {
                likeIcon.classList.remove('fas');
                likeIcon.classList.add('far');
            }

            // Disable like button if not logged in or not a client
            if (!isLoggedIn || userRole !== 'client') {
                likeButton.disabled = true;
                likeButton.style.cursor = 'not-allowed';
                likeIcon.style.color = '#ccc'; // Grey out icon
            } else {
                likeButton.disabled = false;
                likeButton.style.cursor = 'pointer';
                // Restore original color if not liked, or keep solid if liked
                if (!isLiked) {
                    likeIcon.style.color = ''; // Reset to default (from CSS)
                }
            }
        };

        likeButton.addEventListener('click', () => {
            if (!isLoggedIn) {
                alert('Anda harus login untuk menyukai gambar.');
                return;
            }
            if (userRole !== 'client') {
                alert('Hanya klien yang dapat menyukai gambar.');
                return;
            }

            const activeItem = carousel.querySelector('.carousel-item.active');
            if (!activeItem) return;

            const imageId = activeItem.dataset.imageId;
            const isLiked = activeItem.dataset.isLiked === 'True';

            if (isLiked) {
                // Already liked, do nothing on client side, server already handled it
                return;
            }

            fetch(`/api/like/image/${imageId}`, { method: 'POST' })
                .then(res => {
                    if (res.status === 403) {
                        alert('Anda tidak memiliki izin untuk menyukai gambar.');
                        return Promise.reject('Forbidden');
                    }
                    if (!res.ok) {
                        throw new Error('Server merespons dengan kesalahan.');
                    }
                    return res.json();
                })
                .then(data => {
                    activeItem.dataset.likes = data.likes;
                    activeItem.dataset.isLiked = 'True'; // Mark as liked on client side
                    refreshUI();
                })
                .catch(error => console.error("Gagal menyukai gambar:", error));
        });

        carousel.addEventListener('slid.bs.carousel', refreshUI);
        refreshUI();
    };

    document.querySelectorAll('.portfolio-card').forEach(setupPortfolioCard);
});