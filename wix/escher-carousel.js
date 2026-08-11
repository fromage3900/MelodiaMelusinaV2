// Escher Carousel JavaScript
document.addEventListener('DOMContentLoaded', function() {
  const carousel = document.getElementById('escherCarousel');
  if (!carousel) return;

  const track = carousel.querySelector('.carousel-track');
  const slides = carousel.querySelectorAll('.carousel-slide');
  const prevBtn = carousel.querySelector('.carousel-nav.prev');
  const nextBtn = carousel.querySelector('.carousel-nav.next');
  const dotsContainer = carousel.querySelector('.carousel-dots');

  let currentIndex = 0;
  const totalSlides = slides.length;

  // Create dots
  slides.forEach((_, index) => {
    const dot = document.createElement('button');
    dot.className = 'carousel-dot';
    dot.setAttribute('aria-label', `Go to slide ${index + 1}`);
    if (index === 0) dot.classList.add('active');
    dot.addEventListener('click', () => goToSlide(index));
    dotsContainer.appendChild(dot);
  });

  const dots = carousel.querySelectorAll('.carousel-dot');

  function updateCarousel() {
    track.style.transform = `translateX(-${currentIndex * 100}%)`;
    
    // Update dots
    dots.forEach((dot, index) => {
      dot.classList.toggle('active', index === currentIndex);
    });
  }

  function goToSlide(index) {
    currentIndex = index;
    if (currentIndex < 0) currentIndex = totalSlides - 1;
    if (currentIndex >= totalSlides) currentIndex = 0;
    updateCarousel();
  }

  prevBtn.addEventListener('click', () => goToSlide(currentIndex - 1));
  nextBtn.addEventListener('click', () => goToSlide(currentIndex + 1));

  // Auto-advance every 5 seconds
  let autoAdvance = setInterval(() => goToSlide(currentIndex + 1), 5000);

  // Pause on hover
  carousel.addEventListener('mouseenter', () => clearInterval(autoAdvance));
  carousel.addEventListener('mouseleave', () => {
    autoAdvance = setInterval(() => goToSlide(currentIndex + 1), 5000);
  });

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') goToSlide(currentIndex - 1);
    if (e.key === 'ArrowRight') goToSlide(currentIndex + 1);
  });
});
