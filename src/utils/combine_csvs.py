# src/utils/combine_csvs.py
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def combine_csv_files(input_dir: str = 'data', output_name: str = None) -> None:
    """
    Combine all CSV files in the input directory into a single CSV file.
    
    Args:
        input_dir (str): Directory containing CSV files to combine
        output_name (str, optional): Name for output file. If None, generates timestamped name
    """
    try:
        # Convert input_dir to Path object
        data_dir = Path(input_dir)
        
        # Verify directory exists
        if not data_dir.exists():
            logger.error(f"Directory {input_dir} does not exist!")
            return
            
        # Get all CSV files
        csv_files = list(data_dir.glob('*.csv'))
        
        if not csv_files:
            logger.error(f"No CSV files found in {input_dir}")
            return
            
        logger.info(f"Found {len(csv_files)} CSV files to combine")
        
        # Read and combine all CSV files
        dfs = []
        for file in csv_files:
            try:
                logger.info(f"Reading {file.name}")
                df = pd.read_csv(file)
                # Add source file name as a column
                df['Source_File'] = file.stem
                dfs.append(df)
            except Exception as e:
                logger.error(f"Error reading {file.name}: {e}")
                continue
        
        # Combine all dataframes
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Generate output filename if not provided
            if output_name is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_name = f'combined_fifa_players_{timestamp}.csv'
            elif not output_name.endswith('.csv'):
                output_name += '.csv'
            
            # Create output path
            output_path = data_dir / output_name
            
            # Save combined DataFrame
            combined_df.to_csv(output_path, index=False)
            
            logger.info(f"Successfully combined {len(dfs)} files into {output_path}")
            logger.info(f"Total rows: {len(combined_df)}")
            logger.info(f"Columns: {', '.join(combined_df.columns)}")
            
            # Remove duplicates if any
            original_length = len(combined_df)
            combined_df = combined_df.drop_duplicates()
            if len(combined_df) < original_length:
                logger.info(f"Removed {original_length - len(combined_df)} duplicate rows")
                # Save deduplicated data
                dedup_path = data_dir / f'dedup_{output_name}'
                combined_df.to_csv(dedup_path, index=False)
                logger.info(f"Saved deduplicated data to {dedup_path}")
                
        else:
            logger.error("No data frames to combine!")
            
    except Exception as e:
        logger.error(f"Error combining CSV files: {e}")

if __name__ == "__main__":
    combine_csv_files()