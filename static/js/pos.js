// Point of Sale specific functionality

let cart = [];
let currentCustomer = {};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize POS system
    initializePOS();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial products if any
    loadProducts();
});

function initializePOS() {
    // Clear cart on page load
    clearCart();
    
    // Set focus to search input
    const searchInput = document.getElementById('productSearch');
    if (searchInput) {
        searchInput.focus();
    }
    
    // Update cart display
    updateCartDisplay();
    updateTotals();
}

function setupEventListeners() {
    // Product search
    const searchInput = document.getElementById('productSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(searchProducts, 300));
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchProducts();
            }
        });
    }
    
    // Discount amount change
    const discountInput = document.getElementById('discountAmount');
    if (discountInput) {
        discountInput.addEventListener('input', updateTotals);
    }
    
    // Customer info changes
    const customerName = document.getElementById('customerName');
    const customerPhone = document.getElementById('customerPhone');
    
    if (customerName) {
        customerName.addEventListener('input', function() {
            currentCustomer.name = this.value;
        });
    }
    
    if (customerPhone) {
        customerPhone.addEventListener('input', function() {
            currentCustomer.phone = this.value;
        });
    }
}

function searchProducts() {
    const searchInput = document.getElementById('productSearch');
    const query = searchInput.value.trim();
    
    if (query.length < 2) {
        clearSearchResults();
        return;
    }
    
    // Show loading indicator
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = `
        <div class="col-12 text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري البحث...</span>
            </div>
            <p class="mt-2 text-muted">جاري البحث عن المنتجات...</p>
        </div>
    `;
    
    // Search via API
    fetch(`/api/search_products?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(products => {
            displaySearchResults(products);
        })
        .catch(error => {
            console.error('Search error:', error);
            showToast('حدث خطأ في البحث', 'danger');
            clearSearchResults();
        });
}

function displaySearchResults(products) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (products.length === 0) {
        resultsContainer.innerHTML = `
            <div class="col-12 text-center py-4">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h6>لم يتم العثور على نتائج</h6>
                <p class="text-muted">جرب كلمات مختلفة للبحث</p>
            </div>
        `;
        return;
    }
    
    let resultsHTML = '';
    products.forEach(product => {
        resultsHTML += `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card product-card pos-product-card" onclick="addToCart(${JSON.stringify(product).replace(/"/g, '&quot;')})">
                    <div class="card-body p-3">
                        <div class="d-flex">
                            <div class="flex-shrink-0 me-3">
                                ${product.image_url ? 
                                    `<img src="${product.image_url}" class="product-image" alt="${product.name}">` :
                                    '<div class="product-image bg-light d-flex align-items-center justify-content-center"><i class="fas fa-box text-muted"></i></div>'
                                }
                            </div>
                            <div class="flex-grow-1">
                                <h6 class="card-title mb-1">${product.name}</h6>
                                <p class="card-text small text-muted mb-1">${product.name_en || ''}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="h6 text-primary mb-0">${product.price.toFixed(2)} جنيه</span>
                                    <span class="badge ${product.quantity > 0 ? 'bg-success' : 'bg-danger'}">
                                        ${product.quantity > 0 ? product.quantity + ' متوفر' : 'نفد المخزون'}
                                    </span>
                                </div>
                                ${product.barcode ? `<small class="text-muted">الباركود: ${product.barcode}</small>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = resultsHTML;
}

function clearSearchResults() {
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = `
        <div class="col-12 text-center py-4">
            <i class="fas fa-search fa-2x text-muted mb-3"></i>
            <p class="text-muted">ابدأ بالبحث عن المنتجات</p>
        </div>
    `;
}

function addToCart(product) {
    // Check if product is available
    if (product.quantity <= 0) {
        showToast('هذا المنتج غير متوفر في المخزون', 'warning');
        return;
    }
    
    // Check if product already exists in cart
    const existingItemIndex = cart.findIndex(item => item.id === product.id);
    
    if (existingItemIndex !== -1) {
        // Check if we can add more
        if (cart[existingItemIndex].quantity >= product.quantity) {
            showToast('لا يمكن إضافة كمية أكثر من المتوفر في المخزون', 'warning');
            return;
        }
        
        // Increment quantity
        cart[existingItemIndex].quantity += 1;
        cart[existingItemIndex].total = cart[existingItemIndex].quantity * cart[existingItemIndex].price;
    } else {
        // Add new item to cart
        cart.push({
            id: product.id,
            name: product.name,
            name_en: product.name_en,
            price: product.price,
            quantity: 1,
            total: product.price,
            max_quantity: product.quantity,
            image_url: product.image_url
        });
    }
    
    updateCartDisplay();
    updateTotals();
    
    // Show success message
    showToast(`تم إضافة ${product.name} للسلة`, 'success');
    
    // Clear search if needed
    const searchInput = document.getElementById('productSearch');
    if (searchInput) {
        searchInput.value = '';
        clearSearchResults();
    }
}

function removeFromCart(productId) {
    const itemIndex = cart.findIndex(item => item.id === productId);
    if (itemIndex !== -1) {
        const item = cart[itemIndex];
        showToast(`تم حذف ${item.name} من السلة`, 'info');
        cart.splice(itemIndex, 1);
        updateCartDisplay();
        updateTotals();
    }
}

function updateCartQuantity(productId, newQuantity) {
    const item = cart.find(item => item.id === productId);
    if (!item) return;
    
    if (newQuantity <= 0) {
        removeFromCart(productId);
        return;
    }
    
    if (newQuantity > item.max_quantity) {
        showToast('الكمية المطلوبة أكبر من المتوفر في المخزون', 'warning');
        return;
    }
    
    item.quantity = parseInt(newQuantity);
    item.total = item.quantity * item.price;
    
    updateCartDisplay();
    updateTotals();
}

function updateCartDisplay() {
    const cartContainer = document.getElementById('cartItems');
    
    if (cart.length === 0) {
        cartContainer.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-shopping-cart fa-2x mb-2"></i>
                <p>السلة فارغة</p>
            </div>
        `;
        document.getElementById('checkoutBtn').disabled = true;
        return;
    }
    
    let cartHTML = '';
    cart.forEach(item => {
        cartHTML += `
            <div class="cart-item" data-product-id="${item.id}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${item.name}</h6>
                        ${item.name_en ? `<small class="text-muted">${item.name_en}</small>` : ''}
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="removeFromCart(${item.id})" title="حذف من السلة">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="row align-items-center">
                    <div class="col-6">
                        <div class="input-group input-group-sm">
                            <button class="btn btn-outline-secondary" type="button" onclick="updateCartQuantity(${item.id}, ${item.quantity - 1})">
                                <i class="fas fa-minus"></i>
                            </button>
                            <input type="number" class="form-control text-center" value="${item.quantity}" 
                                   min="1" max="${item.max_quantity}" 
                                   onchange="updateCartQuantity(${item.id}, this.value)">
                            <button class="btn btn-outline-secondary" type="button" onclick="updateCartQuantity(${item.id}, ${item.quantity + 1})">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                    <div class="col-6 text-end">
                        <div class="fw-bold">${item.total.toFixed(2)} جنيه</div>
                        <small class="text-muted">${item.price.toFixed(2)} × ${item.quantity}</small>
                    </div>
                </div>
            </div>
        `;
    });
    
    cartContainer.innerHTML = cartHTML;
    document.getElementById('checkoutBtn').disabled = false;
}

function updateTotals() {
    const subtotal = cart.reduce((sum, item) => sum + item.total, 0);
    const discountAmount = parseFloat(document.getElementById('discountAmount').value) || 0;
    const total = subtotal - discountAmount;

    document.getElementById('subtotal').textContent = subtotal.toFixed(2) + ' جنيه';
    document.getElementById('discount').textContent = discountAmount.toFixed(2) + ' جنيه';
    document.getElementById('total').textContent = Math.max(0, total).toFixed(2) + ' جنيه';
}

function clearCart() {
    cart = [];
    currentCustomer = {};
    
    // Reset form fields
    document.getElementById('customerName').value = '';
    document.getElementById('customerPhone').value = '';
    document.getElementById('discountAmount').value = '0';
    document.getElementById('paymentMethod').value = 'cash';
    
    updateCartDisplay();
    updateTotals();
    
    showToast('تم إفراغ السلة', 'info');
}

function processSale() {
    if (cart.length === 0) {
        showToast('السلة فارغة! أضف منتجات قبل إتمام البيع', 'warning');
        return;
    }
    
    const discountAmount = parseFloat(document.getElementById('discountAmount').value) || 0;
    const subtotal = cart.reduce((sum, item) => sum + item.total, 0);
    const total = subtotal - discountAmount;
    
    if (total < 0) {
        showToast('قيمة الخصم أكبر من إجمالي المبلغ', 'warning');
        return;
    }
    
    // Prepare sale data
    const saleData = {
        items: cart.map(item => ({
            product_id: item.id,
            quantity: item.quantity,
            price: item.price
        })),
        customer_name: document.getElementById('customerName').value,
        customer_phone: document.getElementById('customerPhone').value,
        payment_method: document.getElementById('paymentMethod').value,
        discount_amount: discountAmount
    };
    
    // Show loading state
    const checkoutBtn = document.getElementById('checkoutBtn');
    checkoutBtn.disabled = true;
    checkoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> جاري المعالجة...';
    
    // Process sale
    fetch('/api/process_sale', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(saleData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`تم إتمام البيع بنجاح! رقم الفاتورة: ${data.invoice_number}`, 'success');
            
            // Show sale summary modal
            showSaleSummary(data);
            
            // Clear cart
            clearCart();
        } else {
            showToast('خطأ في معالجة البيع: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Sale processing error:', error);
        showToast('حدث خطأ في معالجة البيع', 'danger');
    })
    .finally(() => {
        // Reset checkout button
        checkoutBtn.disabled = false;
        checkoutBtn.innerHTML = '<i class="fas fa-credit-card me-1"></i> إتمام البيع';
    });
}

function showSaleSummary(saleData) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'saleSummaryModal';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-success text-white">
                    <h5 class="modal-title">
                        <i class="fas fa-check-circle me-2"></i>
                        تم إتمام البيع بنجاح
                    </h5>
                </div>
                <div class="modal-body text-center">
                    <div class="mb-4">
                        <i class="fas fa-receipt fa-4x text-success mb-3"></i>
                        <h4>فاتورة رقم: ${saleData.invoice_number}</h4>
                        <h5 class="text-primary">${saleData.total_amount.toFixed(2)} جنيه</h5>
                    </div>
                    <div class="d-grid gap-2">
                        <a href="/invoice/${saleData.sale_id}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-eye me-1"></i>
                            عرض الفاتورة
                        </a>
                        <a href="/print_invoice/${saleData.sale_id}" class="btn btn-outline-primary">
                            <i class="fas fa-print me-1"></i>
                            طباعة الفاتورة
                        </a>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-success" data-bs-dismiss="modal">
                        <i class="fas fa-check me-1"></i>
                        بيع جديد
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Remove modal from DOM when hidden
    modal.addEventListener('hidden.bs.modal', function() {
        modal.remove();
    });
}

function loadProducts() {
    // This could load featured products or recent items
    // For now, we'll just show the search prompt
    clearSearchResults();
}

// Utility function for debouncing search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Keyboard shortcuts specific to POS
document.addEventListener('keydown', function(e) {
    // F1 for search focus
    if (e.key === 'F1') {
        e.preventDefault();
        const searchInput = document.getElementById('productSearch');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
    
    // F2 for barcode scanner
    if (e.key === 'F2') {
        e.preventDefault();
        if (typeof startBarcodeScanner === 'function') {
            startBarcodeScanner();
        }
    }
    
    // F3 for checkout
    if (e.key === 'F3') {
        e.preventDefault();
        const checkoutBtn = document.getElementById('checkoutBtn');
        if (checkoutBtn && !checkoutBtn.disabled) {
            processSale();
        }
    }
    
    // F4 for clear cart
    if (e.key === 'F4') {
        e.preventDefault();
        if (confirm('هل تريد إفراغ السلة؟')) {
            clearCart();
        }
    }
});
