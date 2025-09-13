// Barcode Scanner functionality using HTML5-QRCode library

let html5QrCode = null;
let scannerStarted = false;

// Initialize barcode scanner
function startBarcodeScanner() {
    const modal = new bootstrap.Modal(document.getElementById('barcodeModal'));
    modal.show();

    const modalElement = document.getElementById('barcodeModal');

    // Start scanner when modal is fully shown
    modalElement.addEventListener('shown.bs.modal', function onShown() {
        if (!scannerStarted) {
            initializeScanner();
        }
        modalElement.removeEventListener('shown.bs.modal', onShown);
    });

    // Stop scanner when modal is hidden
    modalElement.addEventListener('hidden.bs.modal', function onHidden() {
        stopScanner();
        modalElement.removeEventListener('hidden.bs.modal', onHidden);
    });
}

function initializeScanner() {
    const qrCodeReader = document.getElementById('qr-reader');

    if (!qrCodeReader) {
        console.error('QR reader element not found');
        return;
    }

    html5QrCode = new Html5Qrcode("qr-reader");

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
        supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA]
    };

    // Start scanning
    html5QrCode.start(
        { facingMode: "environment" }, // Use back camera
        config,
        onScanSuccess,
        onScanFailure
    ).then(() => {
        scannerStarted = true;
        console.log('Barcode scanner started successfully');
    }).catch(err => {
        console.error('Failed to start barcode scanner:', err);
        showScannerError('فشل في بدء تشغيل الماسح الضوئي. تأكد من منح الإذن للكاميرا.');
        showManualBarcodeInput();
    });
}

function stopScanner() {
    if (html5QrCode && scannerStarted) {
        html5QrCode.stop().then(() => {
            scannerStarted = false;
            console.log('Barcode scanner stopped');
        }).catch(err => {
            console.error('Error stopping scanner:', err);
        });
    }
}

function onScanSuccess(decodedText, decodedResult) {
    console.log('Barcode scanned:', decodedText);

    // Stop the scanner
    stopScanner();

    // Close the modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('barcodeModal'));
    if (modal) modal.hide();

    // Process the scanned barcode
    processScannedBarcode(decodedText);
}

function onScanFailure(error) {
    console.debug('Scan failure:', error);
}

function processScannedBarcode(barcode) {
    console.log("Processing barcode:", barcode);

    // Fill the search input if exists
    const searchInput = document.getElementById('productSearch');
    if (searchInput) {
        searchInput.value = barcode;
        if (typeof searchProducts === "function") {
            searchProducts();
        }
    }

    // Show loading
    showToast('جاري البحث عن المنتج...', 'info');

    // Search for product by barcode
    fetch(`/api/get_product_by_barcode/${encodeURIComponent(barcode)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showToast('المنتج غير موجود: ' + barcode, 'warning');
            } else {
                showToast(`تم العثور على المنتج: ${data.name}`, 'success');

                if (window.location.pathname.includes('pos') && typeof addToCart === 'function') {
                    addToCart(data);
                } else {
                    displayProductInfo(data);
                }
            }
        })
        .catch(error => {
            console.error('Error fetching product:', error);
            showToast('حدث خطأ في البحث عن المنتج', 'danger');
        });
}

function showScannerError(message) {
    const qrReader = document.getElementById('qr-reader');
    qrReader.innerHTML = `
        <div class="alert alert-warning text-center">
            <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
            <h6>خطأ في الماسح الضوئي</h6>
            <p>${message}</p>
        </div>
    `;
}

function showManualBarcodeInput() {
    const qrReader = document.getElementById('qr-reader');
    qrReader.innerHTML = `
        <div class="text-center">
            <div class="alert alert-info">
                <i class="fas fa-keyboard fa-2x mb-3"></i>
                <h6>إدخال الباركود يدوياً</h6>
                <p>أدخل رقم الباركود أدناه</p>
            </div>
            <div class="input-group">
                <input type="text" id="manualBarcode" class="form-control" placeholder="أدخل رقم الباركود">
                <button class="btn btn-primary" onclick="processManualBarcode()">
                    <i class="fas fa-search me-1"></i>
                    بحث
                </button>
            </div>
        </div>
    `;

    setTimeout(() => {
        document.getElementById('manualBarcode').focus();
    }, 100);

    document.getElementById('manualBarcode').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            processManualBarcode();
        }
    });
}

function processManualBarcode() {
    const barcodeInput = document.getElementById('manualBarcode');
    const barcode = barcodeInput.value.trim();

    if (barcode) {
        const modal = bootstrap.Modal.getInstance(document.getElementById('barcodeModal'));
        if (modal) modal.hide();
        processScannedBarcode(barcode);
    } else {
        showToast('يرجى إدخال رقم الباركود', 'warning');
        barcodeInput.focus();
    }
}

function displayProductInfo(product) {
    const productModal = document.createElement('div');
    productModal.className = 'modal fade';
    productModal.id = 'productInfoModal';
    productModal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">معلومات المنتج</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-4">
                            ${product.image_url ? 
                                `<img src="${product.image_url}" class="img-fluid rounded" alt="${product.name}">` :
                                '<div class="bg-light rounded d-flex align-items-center justify-content-center" style="height: 150px;"><i class="fas fa-image fa-3x text-muted"></i></div>'
                            }
                        </div>
                        <div class="col-md-8">
                            <h5>${product.name}</h5>
                            <p class="text-muted">${product.name_en || ''}</p>
                            <table class="table table-sm">
                                <tr><td><strong>الباركود:</strong></td><td>${product.barcode}</td></tr>
                                <tr><td><strong>SKU:</strong></td><td>${product.sku}</td></tr>
                                <tr><td><strong>السعر:</strong></td><td>${product.price.toFixed(2)} جنيه</td></tr>
                                <tr><td><strong>الكمية المتوفرة:</strong></td><td>${product.quantity}</td></tr>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إغلاق</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(productModal);
    const modal = new bootstrap.Modal(productModal);
    modal.show();

    productModal.addEventListener('hidden.bs.modal', function() {
        productModal.remove();
    });
}

// Enhanced barcode detection for hardware scanners (keyboard emulation)
document.addEventListener('DOMContentLoaded', function() {
    let barcodeBuffer = '';
    let lastKeyTime = Date.now();

    document.addEventListener('keypress', function(e) {
        const currentTime = Date.now();

        if (currentTime - lastKeyTime > 100) {
            barcodeBuffer = '';
        }
        lastKeyTime = currentTime;

        barcodeBuffer += e.key;

        if (e.key === 'Enter' && barcodeBuffer.length > 3) {
            const barcode = barcodeBuffer.slice(0, -1);

            if (!['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
                e.preventDefault();
                processScannedBarcode(barcode);
                barcodeBuffer = '';
            }
        }

        if (barcodeBuffer.length > 50) {
            barcodeBuffer = '';
        }
    });
});

// Camera permissions helper
async function checkCameraPermissions() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        stream.getTracks().forEach(track => track.stop());
        return true;
    } catch (error) {
        console.error('Camera permission denied:', error);
        return false;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        checkCameraPermissions().then(hasPermission => {
            if (!hasPermission) {
                console.warn('Camera permissions not granted. Scanner will use manual input fallback.');
            }
        });
    }
});
