/**
 * Minimal JavaScript for global.css components
 * Handles tabs and other interactive elements
 */

(function() {
    'use strict';

    // Tab functionality
    function initTabs() {
        const tabLinks = document.querySelectorAll('[data-toggle="tab"]');
        
        tabLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                const targetId = this.getAttribute('href').substring(1);
                const targetPane = document.getElementById(targetId);
                
                if (!targetPane) return;
                
                // Remove active class from all tabs and panes in this tab group
                const tabList = this.closest('.nav-tabs');
                if (tabList) {
                    tabList.querySelectorAll('.nav-link').forEach(function(l) {
                        l.classList.remove('active');
                    });
                }
                
                // Remove active from all panes
                const tabContent = targetPane.closest('.tab-content');
                if (tabContent) {
                    tabContent.querySelectorAll('.tab-pane').forEach(function(pane) {
                        pane.classList.remove('active', 'show');
                    });
                }
                
                // Add active class to clicked tab and target pane
                this.classList.add('active');
                targetPane.classList.add('active', 'show');
            });
        });
    }

    // Mobile sidebar toggle
    function initMobileSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const mobileToggle = document.getElementById('mobile-sidebar-toggle');
        
        if (mobileToggle && sidebar) {
            mobileToggle.addEventListener('click', function(e) {
                e.preventDefault();
                sidebar.classList.toggle('open');
            });
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initTabs();
            initMobileSidebar();
        });
    } else {
        initTabs();
        initMobileSidebar();
    }
})();
