"""
FreshnessMetricsTracker - Rastrea win-rates y métricas de performance por freshness_score
⭐ P3 Phase - Backtest de Historicidad de Señales
"""

import json
from pathlib import Path
from datetime import datetime


class FreshnessMetricsTracker:
    """Rastrea performance de señales agrupadas por su freshness_score"""
    
    def __init__(self, filename='logs/freshness_metrics.json'):
        """
        Inicializa tracker de métricas
        
        filename: donde persiste los datos de backtest
        """
        self.filename = filename
        self.data = self._load_data()
    
    def _load_data(self):
        """Carga métricas previas o crea nuevas"""
        try:
            path = Path(self.filename)
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return {
            'freshness_ranges': {
                'very_fresh_90_100': {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0},
                'fresh_70_89': {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0},
                'moderate_50_69': {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0},
                'old_20_49': {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0},
                'very_old_0_19': {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0},
            },
            'candles_in_condition': {
                # '1': {...}, '2': {...}, etc
            },
            'overall_stats': {
                'total_trades': 0,
                'total_wins': 0,
                'total_losses': 0,
                'overall_win_rate': 0,
            },
            'last_updated': None
        }
    
    def record_trade(self, freshness_score, candles_in_condition, direction, result, pnl=0):
        """
        Registra resultado de una operación
        
        Args:
            freshness_score: 0-100 (100 = reciente, 0 = viejo)
            candles_in_condition: 1-10 (cuántas velas en condición)
            direction: 'BUY' | 'SELL'
            result: 'WIN' | 'LOSS'
            pnl: profit/loss en pips
        """
        try:
            # Determinar rango de frescura
            if freshness_score >= 90:
                range_key = 'very_fresh_90_100'
            elif freshness_score >= 70:
                range_key = 'fresh_70_89'
            elif freshness_score >= 50:
                range_key = 'moderate_50_69'
            elif freshness_score >= 20:
                range_key = 'old_20_49'
            else:
                range_key = 'very_old_0_19'
            
            # Incrementar estadísticas del rango
            if result.upper() == 'WIN':
                self.data['freshness_ranges'][range_key]['wins'] += 1
                self.data['overall_stats']['total_wins'] += 1
            else:
                self.data['freshness_ranges'][range_key]['losses'] += 1
                self.data['overall_stats']['total_losses'] += 1
            
            self.data['freshness_ranges'][range_key]['trades'] += 1
            self.data['overall_stats']['total_trades'] += 1
            
            # Recalcular win rates
            for range_key in self.data['freshness_ranges']:
                trades = self.data['freshness_ranges'][range_key]['trades']
                wins = self.data['freshness_ranges'][range_key]['wins']
                wr = (wins / trades * 100) if trades > 0 else 0
                self.data['freshness_ranges'][range_key]['win_rate'] = round(wr, 2)
            
            # Actualizar win rate general
            total = self.data['overall_stats']['total_trades']
            wins = self.data['overall_stats']['total_wins']
            self.data['overall_stats']['overall_win_rate'] = round((wins / total * 100) if total > 0 else 0, 2)
            
            # Rastrear by candles_in_condition
            candles_key = str(candles_in_condition)
            if candles_key not in self.data['candles_in_condition']:
                self.data['candles_in_condition'][candles_key] = {'trades': 0, 'wins': 0, 'losses': 0}
            
            if result.upper() == 'WIN':
                self.data['candles_in_condition'][candles_key]['wins'] += 1
            else:
                self.data['candles_in_condition'][candles_key]['losses'] += 1
            
            self.data['candles_in_condition'][candles_key]['trades'] += 1
            
            # Actualizar timestamp
            self.data['last_updated'] = datetime.now().isoformat()
            
            # Persistir
            self._save_data()
            
            return True
        except Exception as e:
            print(f"[ERROR] recording trade: {str(e)[:60]}")
            return False
    
    def _save_data(self):
        """Persiste datos a JSON"""
        try:
            path = Path(self.filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[ERROR] saving metrics: {str(e)[:60]}")
    
    def get_summary(self):
        """Retorna resumen legible de métricas"""
        summary = {
            'overall': {
                'trades': self.data['overall_stats']['total_trades'],
                'wins': self.data['overall_stats']['total_wins'],
                'losses': self.data['overall_stats']['total_losses'],
                'win_rate': f"{self.data['overall_stats']['overall_win_rate']:.2f}%"
            },
            'by_freshness': {}
        }
        
        for range_key, stats in self.data['freshness_ranges'].items():
            if stats['trades'] > 0:
                summary['by_freshness'][range_key] = {
                    'trades': stats['trades'],
                    'win_rate': f"{stats['win_rate']:.2f}%"
                }
        
        return summary
    
    def get_best_freshness_range(self):
        """Retorna el rango de frescura con mejor win-rate"""
        best = None
        best_wr = -1
        
        for range_key, stats in self.data['freshness_ranges'].items():
            if stats['trades'] >= 3 and stats['win_rate'] > best_wr:  # Mínimo 3 trades
                best = range_key
                best_wr = stats['win_rate']
        
        if best:
            return {
                'range': best,
                'win_rate': self.data['freshness_ranges'][best]['win_rate'],
                'trades': self.data['freshness_ranges'][best]['trades']
            }
        return None
    
    def log_summary(self):
        """Imprime resumen en formato readable"""
        print(f"\n📊 [FRESHNESS METRICS] - {self.data['last_updated']}")
        print(f"{'='*60}")
        
        summary = self.get_summary()
        print(f"\n🎯 OVERALL:")
        print(f"   Total Trades: {summary['overall']['trades']}")
        print(f"   Wins/Losses: {summary['overall']['wins']}/{summary['overall']['losses']}")
        print(f"   Win Rate: {summary['overall']['win_rate']}")
        
        print(f"\n📈 BY FRESHNESS:")
        for range_key, stats in summary['by_freshness'].items():
            print(f"   {range_key}: {stats['trades']} trades, WR={stats['win_rate']}")
        
        best = self.get_best_freshness_range()
        if best:
            print(f"\n⭐ BEST: {best['range']} ({best['win_rate']:.2f}% on {best['trades']} trades)")
        
        print(f"\n{'='*60}\n")
