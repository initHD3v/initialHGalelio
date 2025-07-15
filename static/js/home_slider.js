document.addEventListener('DOMContentLoaded', () => {
    const sliderTrack = document.querySelector('.home-slider-track');
    if (!sliderTrack) return;

    const slides = Array.from(sliderTrack.children);
    
    // Duplicate slides to create infinite effect
    slides.forEach(slide => {
        sliderTrack.appendChild(slide.cloneNode(true));
    });

    // Re-select all slides after duplication to include cloned nodes
    const allSlides = Array.from(sliderTrack.children);

    // Calculate total width of the original slides + duplicated slides
    const totalSlidesWidth = sliderTrack.scrollWidth / 2; // Half because we duplicated

    // Set animation duration based on total width and desired speed
    // Adjust 0.05 for speed (smaller value = faster)
    const duration = totalSlidesWidth * 0.05; 
    sliderTrack.style.animationDuration = `${duration}s`;

    // Pause animation on hover (optional)
    sliderTrack.addEventListener('mouseover', () => {
        sliderTrack.style.animationPlayState = 'paused';
    });

    sliderTrack.addEventListener('mouseout', () => {
        sliderTrack.style.animationPlayState = 'running';
    });

    // Add hover effect for individual slides
    allSlides.forEach(slide => {
        slide.addEventListener('mouseover', () => {
            allSlides.forEach(otherSlide => {
                if (otherSlide !== slide) {
                    otherSlide.querySelector('img').classList.add('grayscale');
                }
            });
        });

        slide.addEventListener('mouseout', () => {
            allSlides.forEach(otherSlide => {
                otherSlide.querySelector('img').classList.remove('grayscale');
            });
        });
    });
});