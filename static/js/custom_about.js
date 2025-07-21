document.addEventListener('DOMContentLoaded', function() {
    const counterElement = document.getElementById('experience-counter');

    if (counterElement) {
        const target = parseInt(counterElement.getAttribute('data-target'));
        let current = 0;
        const duration = 2000; // Durasi animasi dalam milidetik
        const increment = target / (duration / 10); // Hitung kenaikan per 10ms

        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const animateCounter = () => {
                        if (current < target) {
                            current += increment;
                            if (current > target) current = target; // Pastikan tidak melebihi target
                            counterElement.textContent = Math.floor(current);
                            requestAnimationFrame(animateCounter);
                        } else {
                            counterElement.textContent = target; // Pastikan nilai akhir tepat
                            observer.unobserve(entry.target); // Hentikan observasi setelah animasi selesai
                        }
                    };
                    animateCounter();
                }
            });
        }, { threshold: 0.5 }); // Animasi dimulai ketika 50% elemen terlihat

        observer.observe(counterElement);
    }

    // Parallax Effect for Hero Section
    const heroSection = document.querySelector('.about-hero-new');

    if (heroSection) {
        window.addEventListener('scroll', () => {
            const scrollPosition = window.scrollY;
            // Adjust the multiplier for stronger/weaker parallax effect
            heroSection.style.backgroundPositionY = -scrollPosition * 0.3 + 'px';
        });
    }

    // Hero Image Upload Functionality for Admin
    const heroImageUploadInput = document.getElementById('hero-image-upload');
    const changeHeroImageBtn = document.getElementById('change-hero-image-btn');

    if (heroImageUploadInput && changeHeroImageBtn) {
        heroImageUploadInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const formData = new FormData();
                formData.append('hero_image', file);

                fetch('/admin/upload_hero_image', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update the background image of the hero section
                        if (heroSection) {
                            heroSection.style.backgroundImage = `linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url('${data.new_image_url}')`;
                        }
                        alert(data.message); // Or use a more sophisticated notification
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error uploading hero image:', error);
                    alert('An error occurred during upload.');
                });
            }
        });
    }

    // Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl)
    })
});
