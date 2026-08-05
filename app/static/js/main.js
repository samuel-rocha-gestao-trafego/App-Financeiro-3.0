document.addEventListener('DOMContentLoaded', function () {
  // Ativação automática de tooltips do Bootstrap
  const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipElements.forEach(el => new bootstrap.Tooltip(el));

  // Oculta alertas automaticamente após 5 segundos
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });
});