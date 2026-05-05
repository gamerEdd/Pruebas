"""
🤖 CAPA 3: DECISION ENGINE - Integrador de Dataset Profesional
Une los datos con especialistas de compra/venta
"""

import numpy as np
from datetime import datetime, timedelta


class DatasetLearningEngine:
    """
    Motor que analiza el dataset profesional
    para mejorar decisiones de compra/venta
    """
    
    def __init__(self, dataset_manager, log_callback=None):
        self.dataset_manager = dataset_manager
        self.log_callback = log_callback
        self.learning_history = []
        self.pattern_recognition = {}
        
    def log(self, message, level='info'):
        if self.log_callback:
            self.log_callback(message, level)
    
    def analyze_dataset_patterns(self):
        """
        🧠 Analiza patrones en los 1000 snapshots
        - Identifica condiciones de compra exitosas
        - Identifica condiciones de venta exitosas
        - Aprende correlaciones
        """
        
        df = self.dataset_manager.get_dataframe()
        if df is None or len(df) < 50:
            self.log("⚠️ Dataset insuficiente para análisis de patrones", 'warning')
            return None
        
        patterns = {
            'buy_conditions': self._extract_buy_patterns(df),
            'sell_conditions': self._extract_sell_patterns(df),
            'correlation_matrix': self._calculate_correlations(df),
            'session_performance': self._analyze_by_session(df),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.learning_history.append(patterns)
        return patterns
    
    def _extract_buy_patterns(self, df):
        """Extrae patrones de compra exitosa del dataset"""
        
        # Condiciones ideales de compra
        buy_patterns = {
            'rsi_oversold': {
                'threshold': 35,
                'count': len(df[df['rsi_14'] < 35]),
                'avg_return_next_5': 0,
            },
            'ema_bullish_cross': {
                'count': len(df[df['ema_ratio_9_21'] > 1.0]),
                'avg_imbalance': df[df['ema_ratio_9_21'] > 1.0]['order_imbalance'].mean(),
            },
            'high_volume': {
                'threshold': df['tick_volume'].quantile(0.75),
                'count': len(df[df['tick_volume'] > df['tick_volume'].quantile(0.75)]),
            },
            'low_spread': {
                'avg_spread': df['spread_normalized'].mean(),
                'optimal_count': len(df[df['spread_normalized'] < df['spread_normalized'].quantile(0.25)]),
            },
        }
        
        return buy_patterns
    
    def _extract_sell_patterns(self, df):
        """Extrae patrones de venta exitosa del dataset"""
        
        sell_patterns = {
            'rsi_overbought': {
                'threshold': 65,
                'count': len(df[df['rsi_14'] > 65]),
                'avg_return_next_5': 0,
            },
            'ema_bearish_cross': {
                'count': len(df[df['ema_ratio_9_21'] < 1.0]),
                'avg_imbalance': df[df['ema_ratio_9_21'] < 1.0]['order_imbalance'].mean(),
            },
            'high_volume': {
                'threshold': df['tick_volume'].quantile(0.75),
                'count': len(df[df['tick_volume'] > df['tick_volume'].quantile(0.75)]),
            },
            'sell_volume_dominance': {
                'sell_ratio': (df['sell_volume'] > df['buy_volume']).sum() / len(df),
                'count': (df['sell_volume'] > df['buy_volume']).sum(),
            },
        }
        
        return sell_patterns
    
    def _calculate_correlations(self, df):
        """Calcula matriz de correlación para features numéricas"""
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            
            # Retorna correlaciones más significativas (> 0.5)
            significant_corr = {}
            for col1 in corr_matrix.columns:
                for col2 in corr_matrix.columns:
                    if col1 != col2:
                        corr_val = corr_matrix.loc[col1, col2]
                        if abs(corr_val) > 0.5:
                            significant_corr[f"{col1}_vs_{col2}"] = round(corr_val, 3)
            
            return significant_corr
        
        return {}
    
    def _analyze_by_session(self, df):
        """Analiza rendimiento por sesión de trading"""
        
        session_stats = {}
        
        for session in df['session'].unique():
            session_df = df[df['session'] == session]
            if len(session_df) > 0:
                session_stats[session] = {
                    'count': len(session_df),
                    'avg_rsi': session_df['rsi_14'].mean(),
                    'avg_volume': session_df['tick_volume'].mean(),
                    'avg_spread': session_df['spread_normalized'].mean(),
                    'volatility': session_df['volatility_5'].mean(),
                    'avg_imbalance': session_df['order_imbalance'].mean(),
                }
        
        return session_stats
    
    def get_learning_insights(self):
        """Obtiene insights que mejoran decisiones de especialistas"""
        
        if not self.learning_history:
            return None
        
        latest_patterns = self.learning_history[-1]
        
        insights = {
            'best_buy_conditions': self._get_best_buy_conditions(latest_patterns),
            'best_sell_conditions': self._get_best_sell_conditions(latest_patterns),
            'session_recommendations': self._get_session_recommendations(latest_patterns),
            'risk_parameters': self._calculate_risk_parameters(),
        }
        
        return insights
    
    def _get_best_buy_conditions(self, patterns):
        """Recomienda mejores condiciones para compra"""
        
        buy_cond = patterns.get('buy_conditions', {})
        
        return {
            'requires_rsi_oversold': buy_cond.get('rsi_oversold', {}).get('count', 0) > 50,
            'requires_bullish_ema': buy_cond.get('ema_bullish_cross', {}).get('count', 0) > 50,
            'optimal_volume': 'high' if buy_cond.get('high_volume', {}).get('count', 0) > 50 else 'normal',
            'prefer_tight_spreads': True,
        }
    
    def _get_best_sell_conditions(self, patterns):
        """Recomienda mejores condiciones para venta"""
        
        sell_cond = patterns.get('sell_conditions', {})
        
        return {
            'requires_rsi_overbought': sell_cond.get('rsi_overbought', {}).get('count', 0) > 50,
            'requires_bearish_ema': sell_cond.get('ema_bearish_cross', {}).get('count', 0) > 50,
            'requires_sell_volume': sell_cond.get('sell_volume_dominance', {}).get('sell_ratio', 0) > 0.5,
        }
    
    def _get_session_recommendations(self, patterns):
        """Recomienda mejor sesión para trading basado en histórico"""
        
        session_stats = patterns.get('session_performance', {})
        
        # Sesión con menor spread (mejor liquidez)
        best_session = min(
            session_stats.items(),
            key=lambda x: x[1].get('avg_spread', float('inf')),
            default=('London', {})
        )[0]
        
        return {
            'best_liquidity_session': best_session,
            'session_stats': session_stats,
        }
    
    def _calculate_risk_parameters(self):
        """Calcula parámetros de riesgo basados en volatilidad histórica"""
        
        df = self.dataset_manager.get_dataframe()
        if df is None or len(df) == 0:
            return None
        
        volatility_stats = {
            'avg_volatility_5': df['volatility_5'].mean(),
            'max_volatility_5': df['volatility_5'].max(),
            'p95_volatility': df['volatility_5'].quantile(0.95),
            'avg_spread': df['spread_normalized'].mean(),
            'avg_atr': df['atr_normalized'].mean(),
        }
        
        # Recomendar SL/TP basado en volatilidad
        return {
            'volatility_stats': volatility_stats,
            'suggested_sl_atr_multiple': 1.5,  # SL = 1.5 x ATR
            'suggested_tp_atr_multiple': 2.5,  # TP = 2.5 x ATR
            'max_loss_per_trade': 2.0,  # Máx $2 de pérdida
        }


if __name__ == "__main__":
    # 🚀 Test: python dataset_learning_engine.py
    from professional_dataset_manager import ProfessionalDatasetManager
    
    manager = ProfessionalDatasetManager()
    engine = DatasetLearningEngine(manager)
    
    patterns = engine.analyze_dataset_patterns()
    print("\\n🧠 Patrones analizados:")
    print(f"  - Condiciones de compra: {len(patterns.get('buy_conditions', {}))}")
    print(f"  - Condiciones de venta: {len(patterns.get('sell_conditions', {}))}")
    
    insights = engine.get_learning_insights()
    print("\\n💡 Insights de aprendizaje:")
    import json
    print(json.dumps(insights, indent=2, default=str))
