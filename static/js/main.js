// The Perspective Shift - Gen Z/Millennial Enhanced JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Initialize all features
    initializeThemeToggle();
    initializeFormValidation();
    initializeAnimations();
    initializeFlashMessages();
    initializeParticles();
    setupSimpleLoadingState();
    autoResizeTextarea();
    initializeKeyboardShortcuts();
    initializeQuoteActions();
    initializeSharing();
});

// Dark Mode Toggle - Essential Gen Z Feature
function initializeThemeToggle() {
    // Create theme toggle button
    const themeToggle = document.createElement('button');
    themeToggle.className = 'theme-toggle';
    themeToggle.setAttribute('aria-label', 'Toggle dark mode');
    themeToggle.innerHTML = `
        <svg class="sun-icon" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd"/>
        </svg>
        <svg class="moon-icon" fill="currentColor" viewBox="0 0 20 20" style="display: none;">
            <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/>
        </svg>
    `;

    document.body.appendChild(themeToggle);

    // Check for saved theme preference or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    // Toggle theme on click
    themeToggle.addEventListener('click', function () {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
        showToast(`Switched to ${newTheme} mode ✨`);
    });

    function updateThemeIcon(theme) {
        const sunIcon = themeToggle.querySelector('.sun-icon');
        const moonIcon = themeToggle.querySelector('.moon-icon');

        if (theme === 'dark') {
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'block';
        } else {
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
        }
    }
}

function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');

    Array.from(forms).forEach(form => {
        form.addEventListener('submit', function (event) {
            const textarea = form.querySelector('textarea[required]');

            if (!form.checkValidity() || !textarea.value.trim()) {
                event.preventDefault();
                event.stopPropagation();

                if (!textarea.value.trim()) {
                    textarea.setCustomValidity('Please share what\'s on your mind.');
                } else {
                    textarea.setCustomValidity('');
                }
            }

            form.classList.add('was-validated');
        });

        // Clear validation on input
        const textarea = form.querySelector('textarea[required]');
        if (textarea) {
            textarea.addEventListener('input', function () {
                if (this.value.trim()) {
                    this.setCustomValidity('');
                } else {
                    this.setCustomValidity('Please share what\'s on your mind.');
                }

                // Remove validation classes if user is typing
                if (form.classList.contains('was-validated')) {
                    form.classList.remove('was-validated');
                }
            });
        }
    });
}

function initializeAnimations() {
    // Enhanced scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                // Stagger animation for multiple cards
                setTimeout(() => {
                    entry.target.classList.add('fade-in');
                }, index * 200);
            }
        });
    }, observerOptions);

    // Observe all quote cards
    const quoteCards = document.querySelectorAll('.quote-card:not(.fade-in)');
    quoteCards.forEach(card => {
        observer.observe(card);
    });

    // Smooth scrolling for internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function initializeFlashMessages() {
    // Auto-dismiss flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

function initializeParticles() {
    // Enhanced particle system
    const particlesContainer = document.querySelector('.particles-container');

    if (!particlesContainer) return;

    // Create additional particles dynamically with colors from CSS variables
    const colors = ['--coral', '--mint', '--sky', '--lavender', '--golden', '--peach'];

    for (let i = 0; i < 6; i++) {
        setTimeout(() => {
            createEnhancedParticle(particlesContainer, colors[i % colors.length]);
        }, i * 2000);
    }
}

function createEnhancedParticle(container, colorVar) {
    const particle = document.createElement('div');
    particle.className = 'particle';

    // Random position and size
    particle.style.left = Math.random() * 100 + '%';
    particle.style.width = (20 + Math.random() * 40) + 'px';
    particle.style.height = particle.style.width;

    // Use CSS variable color
    particle.style.background = `radial-gradient(circle, var(${colorVar}), transparent)`;

    // Random animation delay
    particle.style.animationDelay = Math.random() * 10 + 's';
    particle.style.animationDuration = (25 + Math.random() * 10) + 's';

    container.appendChild(particle);

    // Remove particle after animation cycle
    setTimeout(() => {
        if (particle.parentNode) {
            particle.parentNode.removeChild(particle);
        }
    }, 35000);
}

// Enhanced textarea auto-resize with smooth animation
function autoResizeTextarea() {
    const textareas = document.querySelectorAll('.perspective-input');

    textareas.forEach(textarea => {
        // Set initial height
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';

        textarea.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });

        // Add focus effects
        textarea.addEventListener('focus', function () {
            this.style.transition = 'all 0.2s ease';
        });

        textarea.addEventListener('blur', function () {
            this.style.transition = 'all 0.2s ease';
        });
    });
}

function setupSimpleLoadingState() {
    const form = document.querySelector('form[action*="shift"]');

    if (!form) return;

    form.addEventListener('submit', function (event) {
        const submitBtn = form.querySelector('.submit-button');
        const textarea = form.querySelector('textarea[required]');

        // Only proceed if form is valid
        if (textarea && textarea.value.trim()) {
            if (submitBtn) {
                submitBtn.innerHTML = `
                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24" style="animation: spin 1s linear infinite; vertical-align: middle; margin-right: 0.5em;">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.3"/>
                        <path fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                    Processing... Please wait
                `;
                submitBtn.disabled = true;
                submitBtn.setAttribute('aria-busy', 'true');
            }
        }
    });
}

// Keyboard shortcuts for power users
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function (e) {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const activeElement = document.activeElement;
            if (activeElement.tagName === 'TEXTAREA') {
                const form = activeElement.closest('form');
                if (form) {
                    form.submit();
                }
            }
        }

        // Ctrl/Cmd + D to toggle dark mode
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            const themeToggle = document.querySelector('.theme-toggle');
            if (themeToggle) {
                themeToggle.click();
            }
        }

        // Escape to clear form or close dropdowns
        if (e.key === 'Escape') {
            const activeElement = document.activeElement;
            
            // Close any open dropdowns first
            const openDropdown = document.querySelector('.dropdown-menu.show');
            if (openDropdown) {
                closeAllDropdowns();
                return;
            }
            
            // Then handle form clearing
            if (activeElement.tagName === 'TEXTAREA') {
                activeElement.value = '';
                activeElement.style.height = 'auto';
                activeElement.blur();
                showToast('Form cleared ✨');
            }
        }
        
        // Arrow key navigation for dropdowns
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            const focusedElement = document.activeElement;
            const dropdown = focusedElement.closest('.dropdown-container');
            
            if (dropdown) {
                e.preventDefault();
                const dropdownMenu = dropdown.querySelector('.dropdown-menu');
                const items = Array.from(dropdownMenu.querySelectorAll('.dropdown-item:not([style*="display: none"])'));
                
                if (items.length === 0) return;
                
                const currentIndex = items.indexOf(document.activeElement);
                let nextIndex;
                
                if (e.key === 'ArrowDown') {
                    nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
                } else {
                    nextIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
                }
                
                items[nextIndex].focus();
            }
        }
    });
}

// Quote Actions Enhancement
function initializeQuoteActions() {
    // Initialize copy functionality
    initializeCopyButtons();
}

// Copy to Clipboard Functionality
function initializeCopyButtons() {
    // Initialize copy options dropdowns
    initializeCopyOptions();

    // Initialize copy all button
    initializeCopyAllButton();
}

function initializeCopyOptions() {
    const copyOptionsButtons = document.querySelectorAll('.copy-options-button');
    const copyOptionItems = document.querySelectorAll('.copy-option-item');

    // Toggle dropdown visibility
    copyOptionsButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.stopPropagation();
            const parent = this.closest('.copy-options');
            const isOpen = parent.classList.contains('open');

            // Close all other dropdowns
            document.querySelectorAll('.copy-options.open').forEach(dropdown => {
                dropdown.classList.remove('open');
            });

            // Toggle current dropdown
            if (!isOpen) {
                parent.classList.add('open');
            }
        });
    });

    // Handle copy option selection
    copyOptionItems.forEach(item => {
        item.addEventListener('click', async function () {
            try {
                const format = this.dataset.format;
                const quote = this.dataset.quote;
                const attribution = this.dataset.attribution;
                const perspective = this.dataset.perspective;
                const context = this.dataset.context;

                let textToCopy;

                switch (format) {
                    case 'markdown':
                        textToCopy = generateMarkdown(quote, attribution, perspective, context);
                        break;
                    case 'plain':
                        textToCopy = generatePlainText(quote, attribution, perspective, context);
                        break;
                    case 'quote-only':
                        textToCopy = `"${quote}" — ${attribution}`;
                        break;
                    default:
                        textToCopy = generateMarkdown(quote, attribution, perspective, context);
                }

                await copyToClipboard(textToCopy);
                showToast(`Quote copied as ${format}! 📋`, 'success');

                // Close dropdown
                this.closest('.copy-options').classList.remove('open');

            } catch (error) {
                console.error('Copy failed:', error);
                showToast('Failed to copy quote. Please try again.', 'error');
            }
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function () {
        document.querySelectorAll('.copy-options.open').forEach(dropdown => {
            dropdown.classList.remove('open');
        });
    });
}

function initializeCopyAllButton() {
    const copyAllButton = document.querySelector('.copy-all-button');

    if (!copyAllButton) return;

    copyAllButton.addEventListener('click', async function () {
        try {
            // Get all quote cards
            const quoteCards = document.querySelectorAll('.quote-card');
            let allQuotesMarkdown = '';

            quoteCards.forEach((card, index) => {
                // Extract quote data from the card
                const quoteText = card.querySelector('.quote-text').textContent.replace(/"/g, '').trim();
                const attribution = card.querySelector('.quote-attribution').textContent.replace(/—\s*/, '').trim();
                const perspective = card.querySelector('.detail-section:first-child .detail-text').textContent.trim();
                const context = card.querySelector('.detail-section:last-child .detail-text').textContent.trim();

                const quoteMarkdown = generateMarkdown(quoteText, attribution, perspective, context);

                if (index > 0) {
                    allQuotesMarkdown += '\n\n---\n\n';
                }
                allQuotesMarkdown += quoteMarkdown;
            });

            await copyToClipboard(allQuotesMarkdown);
            showCopyAllSuccess(this);
            showToast(`All ${quoteCards.length} quotes copied as markdown! 📋`, 'success');

        } catch (error) {
            console.error('Copy all failed:', error);
            showToast('Failed to copy all quotes. Please try again.', 'error');
        }
    });
}

function generateMarkdown(quote, attribution, perspective, context) {
    return `> "${quote}"
— **${attribution}**

## Perspective
${perspective}

## Context
${context}`;
}

function generatePlainText(quote, attribution, perspective, context) {
    return `"${quote}"
— ${attribution}

Perspective:
${perspective}

Context:
${context}`;
}

async function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        // Modern Clipboard API
        await navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
        } finally {
            document.body.removeChild(textArea);
        }
    }
}

function showCopyAllSuccess(button) {
    const originalHTML = button.innerHTML;
    const originalClass = button.className;

    button.classList.add('copied');
    button.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
        </svg>
        All Copied!
    `;

    // Reset after 3 seconds
    setTimeout(() => {
        button.className = originalClass;
        button.innerHTML = originalHTML;
    }, 3000);
}

function showToast(message, type = 'success') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());

    // Create new toast
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    // Show toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);

    // Hide and remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Add some CSS for the spinner animation
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Social Media Sharing Manager
class SocialShareManager {
    constructor(quoteData) {
        this.quote = quoteData.text;
        this.attribution = quoteData.attribution;
        this.imageUrl = quoteData.imageUrl;
        this.shareUrl = quoteData.shareUrl;
        this.quoteId = quoteData.id;
    }

    async shareToX() {
        const text = `"${this.quote}" - ${this.attribution} #wisdom #quotes`;
        const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(this.shareUrl)}`;
        this.trackShare('x');
        this.openShareWindow(url, 550, 420);
    }

    async shareToLinkedIn() {
        // Create LinkedIn post with prefilled text
        const shareText = `"${this.quote}" - ${this.attribution}

Discover more wisdom quotes that match your moment at The Perspective Shift 🔗`;
        
        const url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(this.shareUrl)}&summary=${encodeURIComponent(shareText)}`;
        this.trackShare('linkedin');
        this.openShareWindow(url, 520, 570);
    }

    async shareViaWebAPI() {
        if (!navigator.share) return false;
        
        try {
            const shareData = {
                title: 'Wisdom Quote from PerspectiveShifter',
                text: `"${this.quote}" - ${this.attribution}`,
                url: this.shareUrl
            };

            await navigator.share(shareData);
            this.trackShare('native');
            return true;
        } catch (error) {
            console.log('Web Share API failed:', error);
            return false;
        }
    }

    downloadForInstagram() {
        // Create download link for image
        const link = document.createElement('a');
        link.href = this.imageUrl;
        link.download = `wisdom-quote-${this.quoteId}.png`;
        link.click();
        
        // Copy quote text to clipboard
        const instagramText = `"${this.quote}" - ${this.attribution} #wisdom #quotes`;
        copyToClipboard(instagramText);
        
        this.trackShare('instagram');
        this.showInstagramGuidance();
    }

    trackShare(platform) {
        // Privacy-centric tracking - no personal data, just aggregate counts
        fetch(UrlHelpers.getTrackUrl(this.quoteId), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: platform })
        }).catch(() => {}); // Fail silently
        
        // Update UI counter immediately
        this.updateShareCounter();
    }

    updateShareCounter() {
        const counter = document.querySelector('.share-stats');
        if (counter) {
            const current = parseInt(counter.textContent.match(/\d+/)?.[0]) || 0;
            counter.textContent = `${current + 1} quotes shared`;
        }
    }

    openShareWindow(url, width, height) {
        const left = (screen.width - width) / 2;
        const top = (screen.height - height) / 2;
        window.open(url, '_blank', `width=${width},height=${height},left=${left},top=${top}`);
    }

    showInstagramGuidance() {
        showToast('Image downloaded & quote copied! Open Instagram → Create Story → Add photo', 'success');
    }
}

// New Dropdown Management Functions
function toggleShareDropdown(button) {
    const container = button.closest('.dropdown-container');
    const dropdown = container.querySelector('.dropdown-menu');
    const isOpen = dropdown.classList.contains('show');
    
    // Close all other dropdowns first
    closeAllDropdowns();
    
    if (!isOpen) {
        dropdown.classList.add('show');
        button.setAttribute('aria-expanded', 'true');
    }
}

function closeAllDropdowns() {
    document.querySelectorAll('.dropdown-menu').forEach(dropdown => {
        dropdown.classList.remove('show');
    });
    document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
        toggle.setAttribute('aria-expanded', 'false');
    });
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.dropdown-container')) {
        closeAllDropdowns();
    }
});

// New Three-Button Functions
function copyQuoteText(button) {
    const quote = button.dataset.quote;
    const attribution = button.dataset.attribution;
    const text = `"${quote}" - ${attribution}`;
    
    copyToClipboard(text);
    
    // Track copy action
    const card = button.closest('.quote-card');
    const quoteId = card.dataset.quoteId;
    trackShareAction(quoteId, 'copy');
    
    showToast('Quote copied to clipboard!', 'success');
}

function downloadQuoteImage(button) {
    const quoteId = button.dataset.quoteId;
    const attribution = button.dataset.attribution;
    
    // Construct image URL using URL helper
    const imageUrl = UrlHelpers.getSocialMediaImageUrl(quoteId);
    
    // Create download link
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `wisdom-quote-${attribution.replace(/\s+/g, '-')}-${quoteId}.png`;
    link.click();
    
    // Track download action
    trackShareAction(quoteId, 'download');
    
    showToast('Image downloaded!', 'success');
}

// Enhanced Instagram sharing workflow
function shareToInstagramStory(button) {
    const card = button.closest('.quote-card');
    const quoteId = card.dataset.quoteId;
    const quote = card.querySelector('.quote-text').textContent.replace(/"/g, '').trim();
    const attribution = card.querySelector('.quote-attribution').textContent.replace(/—\s*/, '').trim();
    
    // 1. Download with descriptive filename
    const imageUrl = UrlHelpers.getSocialMediaImageUrl(quoteId);
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `wisdom-quote-${attribution.replace(/\s+/g, '-')}-${quoteId}.png`;
    link.click();
    
    // 2. Copy formatted text with hashtags
    const instagramText = `"${quote}" - ${attribution}\n\n#wisdom #quotes #perspective`;
    copyToClipboard(instagramText);
    
    // 3. Show enhanced instructions
    showInstagramInstructions();
    
    // 4. Track with specific action
    trackShareAction(quoteId, 'instagram');
    
    // Close dropdown
    closeAllDropdowns();
}

function showInstagramInstructions() {
    showToast(`✓ Image downloaded & quote copied!

Next steps:
1. Open Instagram
2. Create new Story  
3. Add your downloaded image
4. Paste the quote text`, 'instagram-instructions', 6000);
}

// Enhanced sharing functions for dropdown items
function shareViaWebAPI(button) {
    const card = button.closest('.quote-card');
    const quoteId = card.dataset.quoteId;
    const quote = card.querySelector('.quote-text').textContent.replace(/"/g, '').trim();
    const attribution = card.querySelector('.quote-attribution').textContent.replace(/—\s*/, '').trim();
    const shareUrl = UrlHelpers.getAbsoluteUrl(UrlHelpers.getShareUrl(quoteId));
    
    if (!navigator.share) {
        showToast('Native sharing not supported on this device', 'error');
        return;
    }
    
    const shareData = {
        title: 'Wisdom Quote from PerspectiveShifter',
        text: `"${quote}" - ${attribution}`,
        url: shareUrl
    };
    
    navigator.share(shareData)
        .then(() => {
            trackShareAction(quoteId, 'native');
            showToast('Quote shared!', 'success');
        })
        .catch((error) => {
            console.log('Web Share API failed:', error);
            showToast('Sharing cancelled', 'info');
        });
    
    closeAllDropdowns();
}

function shareToX(button) {
    const card = button.closest('.quote-card');
    const quoteId = card.dataset.quoteId;
    const quote = card.querySelector('.quote-text').textContent.replace(/"/g, '').trim();
    const attribution = card.querySelector('.quote-attribution').textContent.replace(/—\s*/, '').trim();
    const shareUrl = UrlHelpers.getAbsoluteUrl(UrlHelpers.getShareUrl(quoteId));
    
    const text = `"${quote}" - ${attribution} #wisdom #quotes`;
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareUrl)}`;
    
    trackShareAction(quoteId, 'x');
    openShareWindow(url, 550, 420);
    closeAllDropdowns();
}

function shareToLinkedIn(button) {
    const card = button.closest('.quote-card');
    const quoteId = card.dataset.quoteId;
    const shareUrl = UrlHelpers.getAbsoluteUrl(UrlHelpers.getShareUrl(quoteId));
    
    // LinkedIn 2024: Only Open Graph tags work, no URL parameters for prefill
    const linkedinUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
    
    trackShareAction(quoteId, 'linkedin');
    openShareWindow(linkedinUrl, 520, 570);
    closeAllDropdowns();
}

// Helper functions
function trackShareAction(quoteId, platform) {
    fetch(UrlHelpers.getTrackUrl(quoteId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform: platform })
    }).catch(() => {}); // Fail silently
}

function openShareWindow(url, width, height) {
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;
    window.open(url, '_blank', `width=${width},height=${height},left=${left},top=${top}`);
}

function shouldShowNativeShare() {
    return navigator.share && /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Initialize sharing for quotes (Updated for new layout)
function initializeSharing() {
    const quoteCards = document.querySelectorAll('.quote-card');
    
    quoteCards.forEach(card => {
        // Check for new layout first
        const newActions = card.querySelector('.quote-actions-redesigned');
        if (newActions) {
            // New three-button layout - handled by onclick attributes
            return;
        }
        
        // Legacy layout support
        const shareSection = card.querySelector('.share-section');
        if (!shareSection) return;
        
        // Extract quote data from the card
        const quoteText = card.querySelector('.quote-text').textContent.replace(/"/g, '').trim();
        const attribution = card.querySelector('.quote-attribution').textContent.replace(/—\s*/, '').trim();
        const quoteId = card.dataset.quoteId;
        
        if (!quoteId) return;
        
        const quoteData = {
            text: quoteText,
            attribution: attribution,
            imageUrl: UrlHelpers.getSocialMediaImageUrl(quoteId),
            shareUrl: UrlHelpers.getAbsoluteUrl(UrlHelpers.getShareUrl(quoteId)),
            id: quoteId
        };
        
        const shareManager = new SocialShareManager(quoteData);
        
        // Attach event listeners to share buttons
        const nativeShareBtn = shareSection.querySelector('[data-share="native"]');
        const xShareBtn = shareSection.querySelector('[data-share="x"]');
        const linkedinShareBtn = shareSection.querySelector('[data-share="linkedin"]');
        const instagramShareBtn = shareSection.querySelector('[data-share="instagram"]');
        
        if (nativeShareBtn) {
            nativeShareBtn.addEventListener('click', () => shareManager.shareViaWebAPI());
        }
        
        if (xShareBtn) {
            xShareBtn.addEventListener('click', () => shareManager.shareToX());
        }
        
        if (linkedinShareBtn) {
            linkedinShareBtn.addEventListener('click', () => shareManager.shareToLinkedIn());
        }
        
        if (instagramShareBtn) {
            instagramShareBtn.addEventListener('click', () => shareManager.downloadForInstagram());
        }
    });
}
