import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { colors } from '../styles/colors';
import { FaCheck } from 'react-icons/fa';

const Breadcrumb = () => {
  const location = useLocation();
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

  // Define breadcrumb steps based on route
  const getBreadcrumbSteps = () => {
    const path = location.pathname;
    const steps = [];

    // Step 1: Transaction Type
    const isTransactionType = path === '/transaction-type';
    const isAfterTransactionType = path === '/finance' || path === '/real-time-analysis' || 
      path.startsWith('/check-analysis') || path.startsWith('/paystub-analysis') || 
      path.startsWith('/money-order-analysis') || path.startsWith('/bank-statement-analysis');

    steps.push({
      label: 'Transaction Type',
      path: '/transaction-type',
      stepNumber: 1,
      isCompleted: isAfterTransactionType,
      isActive: isTransactionType,
    });

    // Step 2: Transaction Selection (On Demand or Real Time)
    if (path === '/finance' || path.startsWith('/check-analysis') || 
        path.startsWith('/paystub-analysis') || path.startsWith('/money-order-analysis') || 
        path.startsWith('/bank-statement-analysis')) {
      const isFinance = path === '/finance';
      const isAfterFinance = path.startsWith('/check-analysis') || path.startsWith('/paystub-analysis') || 
        path.startsWith('/money-order-analysis') || path.startsWith('/bank-statement-analysis');

      steps.push({
        label: 'On Demand Transactions',
        path: '/finance',
        stepNumber: 2,
        isCompleted: isAfterFinance,
        isActive: isFinance,
      });

      // Step 3: Analysis Type (if applicable)
      if (isAfterFinance) {
        let analysisLabel = '';
        if (path === '/check-analysis') {
          analysisLabel = 'Check Analysis';
        } else if (path === '/paystub-analysis') {
          analysisLabel = 'Paystub Analysis';
        } else if (path === '/money-order-analysis') {
          analysisLabel = 'Money Order Analysis';
        } else if (path === '/bank-statement-analysis') {
          analysisLabel = 'Bank Statement Analysis';
        }

        if (analysisLabel) {
          steps.push({
            label: analysisLabel,
            path: path,
            stepNumber: 3,
            isCompleted: false,
            isActive: true,
          });
        }
      }
    } else if (path === '/real-time-analysis') {
      steps.push({
        label: 'Real Time Transaction',
        path: '/real-time-analysis',
        stepNumber: 2,
        isCompleted: false,
        isActive: true,
      });
    }

    return steps;
  };

  const steps = getBreadcrumbSteps();

  const breadcrumbStyle = {
    backgroundColor: colors.card,
    borderBottom: `1px solid ${colors.border}`,
    padding: '1.5rem 2.5rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
  };

  const stepContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  };

  const stepItemStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0.5rem',
    textDecoration: 'none',
  };

  const stepIconStyle = (isCompleted, isActive) => ({
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: isCompleted || isActive ? primary : colors.muted,
    color: isCompleted || isActive ? colors.primaryForeground : colors.mutedForeground,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: isCompleted ? '1rem' : '1rem',
    fontWeight: '600',
    transition: 'all 0.3s',
    border: `2px solid ${isCompleted || isActive ? primary : colors.muted}`,
  });

  const stepLabelStyle = (isActive) => ({
    fontSize: '0.875rem',
    fontWeight: isActive ? '700' : '500',
    color: isActive ? colors.foreground : colors.mutedForeground,
    textAlign: 'center',
    whiteSpace: 'nowrap',
    transition: 'color 0.3s',
  });

  const connectorLineStyle = (isCompleted) => ({
    width: '80px',
    height: '2px',
    backgroundColor: isCompleted ? primary : colors.muted,
    transition: 'background-color 0.3s',
  });

  return (
    <nav style={breadcrumbStyle} aria-label="Breadcrumb">
      {steps.map((step, index) => (
        <React.Fragment key={step.path}>
          <div style={stepContainerStyle}>
            {step.isActive ? (
              <div style={stepItemStyle}>
                <div style={stepIconStyle(step.isCompleted, step.isActive)}>
                  {step.isCompleted ? <FaCheck /> : step.stepNumber}
                </div>
                <span style={stepLabelStyle(true)}>{step.label}</span>
              </div>
            ) : (
              <Link to={step.path} style={stepItemStyle}>
                <div 
                  style={stepIconStyle(step.isCompleted, step.isActive)}
                  onMouseEnter={(e) => {
                    if (!step.isCompleted && !step.isActive) {
                      e.currentTarget.style.backgroundColor = primary;
                      e.currentTarget.style.color = colors.primaryForeground;
                      e.currentTarget.style.borderColor = primary;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!step.isCompleted && !step.isActive) {
                      e.currentTarget.style.backgroundColor = colors.muted;
                      e.currentTarget.style.color = colors.mutedForeground;
                      e.currentTarget.style.borderColor = colors.muted;
                    }
                  }}
                >
                  {step.isCompleted ? <FaCheck /> : step.stepNumber}
                </div>
                <span 
                  style={stepLabelStyle(false)}
                  onMouseEnter={(e) => {
                    if (!step.isCompleted && !step.isActive) {
                      e.target.style.color = primary;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!step.isCompleted && !step.isActive) {
                      e.target.style.color = colors.mutedForeground;
                    }
                  }}
                >
                  {step.label}
                </span>
              </Link>
            )}
          </div>
          {index < steps.length - 1 && (
            <div style={connectorLineStyle(step.isCompleted || step.isActive)} />
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

export default Breadcrumb;

