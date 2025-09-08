// Main JavaScript functionality for POS System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add loading animation to buttons on form submit
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // Re-enable button after 10 seconds to prevent permanent disable
                setTimeout(function() {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                }, 10000);
            }
        });
    });

    // Enhance table interactions
    const tableRows = document.querySelectorAll('.table tbody tr');
    tableRows.forEach(function(row) {
        row.addEventListener('click', function() {
            // Remove previous selections
            tableRows.forEach(function(r) {
                r.classList.remove('table-active');
            });
            // Add selection to current row
            this.classList.add('table-active');
        });
    });

    // Search functionality enhancement
    const searchInputs = document.querySelectorAll('input[type="search"], input[name="search"]');
    searchInputs.forEach(function(input) {
        let searchTimeout;
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const searchForm = this.closest('form');
            
            // Auto-submit search after 1 second of no typing
            searchTimeout = setTimeout(function() {
                if (searchForm && input.value.length >= 2) {
                    searchForm.submit();
                }
            }, 1000);
        });
    });

    // Number input enhancements
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(function(input) {
        // Add increment/decrement buttons for quantity inputs
        if (input.name === 'quantity' || input.classList.contains('quantity-input')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'input-group';
            
            const decrementBtn = document.createElement('button');
            decrementBtn.className = 'btn btn-outline-secondary';
            decrementBtn.type = 'button';
            decrementBtn.innerHTML = '<i class="fas fa-minus"></i>';
            decrementBtn.addEventListener('click', function() {
                const currentValue = parseInt(input.value) || 0;
                if (currentValue > (parseInt(input.min) || 0)) {
                    input.value = currentValue - 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
            
            const incrementBtn = document.createElement('button');
            incrementBtn.className = 'btn btn-outline-secondary';
            incrementBtn.type = 'button';
            incrementBtn.innerHTML = '<i class="fas fa-plus"></i>';
            incrementBtn.addEventListener('click', function() {
                const currentValue = parseInt(input.value) || 0;
                const maxValue = parseInt(input.max) || Infinity;
                if (currentValue < maxValue) {
                    input.value = currentValue + 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
            
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(decrementBtn);
            wrapper.appendChild(input);
            wrapper.appendChild(incrementBtn);
        }
    });

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
    });

    // Image preview functionality
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    imageInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create preview image
                    let preview = document.getElementById(input.id + '_preview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.id = input.id + '_preview';
                        preview.className = 'img-thumbnail mt-2';
                        preview.style.maxWidth = '200px';
                        preview.style.maxHeight = '200px';
                        input.parentNode.appendChild(preview);
                    }
                    preview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Alt + P for POS
        if (e.altKey && e.key === 'p') {
            e.preventDefault();
            const posLink = document.querySelector('a[href*="pos"]');
            if (posLink) {
                window.location.href = posLink.href;
            }
        }
        
        // Alt + D for Dashboard
        if (e.altKey && e.key === 'd') {
            e.preventDefault();
            const dashboardLink = document.querySelector('a[href*="dashboard"]');
            if (dashboardLink) {
                window.location.href = dashboardLink.href;
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
        
        // Enter to submit forms (except textarea)
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
            const form = e.target.closest('form');
            if (form && !e.shiftKey && !e.ctrlKey) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    e.preventDefault();
                    submitBtn.click();
                }
            }
        }
    });

    // Confirmation dialogs for dangerous actions
    const dangerousLinks = document.querySelectorAll('a[href*="delete"], button[data-action="delete"]');
    dangerousLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const confirmMessage = this.getAttribute('data-confirm') || 'هل أنت متأكد من هذا الإجراء؟';
            if (confirm(confirmMessage)) {
                if (this.tagName === 'A') {
                    window.location.href = this.href;
                } else {
                    // Handle button actions
                    const form = this.closest('form');
                    if (form) {
                        form.submit();
                    }
                }
            }
        });
    });

    // Auto-refresh for real-time data (dashboard)
    if (window.location.pathname.includes('dashboard')) {
        setInterval(function() {
            // Refresh low stock alerts
            const lowStockSection = document.querySelector('.low-stock-alerts');
            if (lowStockSection) {
                // This would typically fetch updated data via AJAX
                // For now, we'll just add a visual indicator
                const lastUpdate = document.createElement('small');
                lastUpdate.className = 'text-muted';
                lastUpdate.textContent = 'آخر تحديث: ' + new Date().toLocaleTimeString('ar');
                
                const existingUpdate = lowStockSection.querySelector('.last-update');
                if (existingUpdate) {
                    existingUpdate.remove();
                }
                
                lastUpdate.className += ' last-update';
                lowStockSection.appendChild(lastUpdate);
            }
        }, 30000); // Every 30 seconds
    }

    // Print functionality enhancement
    window.printInvoice = function() {
        window.print();
    };

    // Format numbers with Arabic locale
    window.formatCurrency = function(amount) {
        return new Intl.NumberFormat('ar-SA', {
            style: 'currency',
            currency: 'SAR',
            minimumFractionDigits: 2
        }).format(amount);
    };

    // Utility function to show toast notifications
    window.showToast = function(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 start-50 translate-middle-x p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        document.getElementById('toastContainer').appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    };

    // Initialize any existing toasts
    const toastElements = document.querySelectorAll('.toast');
    toastElements.forEach(function(toastEl) {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    });
});

// Chart initialization for dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if Chart.js is loaded and we're on dashboard
    if (typeof Chart !== 'undefined' && document.getElementById('salesChart')) {
        const ctx = document.getElementById('salesChart').getContext('2d');
        
        // Sample data - in real implementation, this would come from the server
        const salesChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة'],
                datasets: [{
                    label: 'المبيعات اليومية',
                    data: [1200, 1900, 3000, 5000, 2000, 3000, 4500],
                    borderColor: 'rgb(13, 110, 253)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            font: {
                                family: 'Segoe UI'
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + ' ر.س';
                            }
                        }
                    }
                }
            }
        });
    }
});

// Service Worker registration for PWA capabilities
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed');
            });
    });
}
