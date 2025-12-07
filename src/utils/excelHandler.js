import * as XLSX from 'xlsx';

/**
 * Excel Import/Export Handler for Quiz Data
 * Exports to and imports from Excel format with full config preservation
 */

/**
 * Export a quiz to Excel format
 * @param {object} quiz - The quiz object to export
 * @returns {Blob} Excel file as blob
 */
export function exportQuizToExcel(quiz) {
  const workbook = XLSX.utils.book_new();
  
  // Sheet 1: Config
  const configData = [
    ['Property', 'Value'],
    ['Quiz Name', quiz.name],
    ['Quiz ID', quiz.id],
    ['Has Timer', quiz.hasTimer ? 'TRUE' : 'FALSE'],
    ['Timer Seconds', quiz.timerSeconds || ''],
    ['Created At', quiz.createdAt],
    ['Version', '1.0']
  ];
  
  const configSheet = XLSX.utils.aoa_to_sheet(configData);
  configSheet['!cols'] = [{ wch: 20 }, { wch: 40 }];
  XLSX.utils.book_append_sheet(workbook, configSheet, 'Config');
  
  // Sheet for each age group
  quiz.ageGroups.forEach((ageGroup, index) => {
    const sheetData = [
      // Header row with age group config
      ['Age Group Config'],
      ['Theme', ageGroup.theme],
      ['Celebration Type', ageGroup.celebrationType],
      [''],
      // Question headers
      ['Set Name', 'Question', 'Option A', 'Option B', 'Option C', 'Option D', 'Correct Answer']
    ];
    
    // Add questions from each set
    ageGroup.sets.forEach(set => {
      set.questions.forEach(question => {
        const correctLetter = ['A', 'B', 'C', 'D'][question.correctIndex];
        sheetData.push([
          set.name,
          question.text,
          question.options[0],
          question.options[1],
          question.options[2],
          question.options[3],
          correctLetter
        ]);
      });
    });
    
    const sheet = XLSX.utils.aoa_to_sheet(sheetData);
    sheet['!cols'] = [
      { wch: 15 },  // Set Name
      { wch: 50 },  // Question
      { wch: 25 },  // Option A
      { wch: 25 },  // Option B
      { wch: 25 },  // Option C
      { wch: 25 },  // Option D
      { wch: 15 }   // Correct
    ];
    
    // Use age group name as sheet name (Excel limits to 31 chars)
    const sheetName = ageGroup.name.substring(0, 31).replace(/[\\\/\?\*\[\]]/g, '_');
    XLSX.utils.book_append_sheet(workbook, sheet, sheetName);
  });
  
  // Generate buffer
  const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
  return new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
}

/**
 * Download quiz as Excel file
 * @param {object} quiz - The quiz to download
 */
export function downloadQuizAsExcel(quiz) {
  const blob = exportQuizToExcel(quiz);
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${quiz.name.replace(/[^a-zA-Z0-9]/g, '_')}_quiz.xlsx`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Import quiz from Excel file
 * @param {File} file - The Excel file to import
 * @returns {Promise<object>} Parsed quiz object
 */
export async function importQuizFromExcel(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        
        // Parse Config sheet
        const configSheet = workbook.Sheets['Config'];
        if (!configSheet) {
          throw new Error('Invalid quiz file: Missing Config sheet');
        }
        
        const configData = XLSX.utils.sheet_to_json(configSheet, { header: 1 });
        const configMap = {};
        configData.forEach(row => {
          if (row[0] && row[1] !== undefined) {
            configMap[row[0]] = row[1];
          }
        });
        
        // Create quiz object
        const quiz = {
          id: configMap['Quiz ID'] || generateId(),
          name: configMap['Quiz Name'] || 'Imported Quiz',
          hasTimer: configMap['Has Timer'] === 'TRUE',
          timerSeconds: configMap['Timer Seconds'] ? parseInt(configMap['Timer Seconds']) : 30,
          createdAt: configMap['Created At'] || new Date().toISOString(),
          ageGroups: []
        };
        
        // Parse age group sheets
        workbook.SheetNames.forEach(sheetName => {
          if (sheetName === 'Config') return;
          
          const sheet = workbook.Sheets[sheetName];
          const sheetData = XLSX.utils.sheet_to_json(sheet, { header: 1 });
          
          // Parse age group config (rows 1-3)
          let theme = 'crescent-moon';
          let celebrationType = 'confetti';
          
          sheetData.forEach((row, index) => {
            if (row[0] === 'Theme' && row[1]) {
              theme = row[1];
            }
            if (row[0] === 'Celebration Type' && row[1]) {
              celebrationType = row[1];
            }
          });
          
          // Find the header row (contains 'Set Name')
          let headerIndex = sheetData.findIndex(row => row[0] === 'Set Name');
          if (headerIndex === -1) {
            console.warn(`No questions found in sheet: ${sheetName}`);
            return;
          }
          
          // Parse questions (rows after header)
          const sets = {};
          for (let i = headerIndex + 1; i < sheetData.length; i++) {
            const row = sheetData[i];
            if (!row[0] || !row[1]) continue; // Skip empty rows
            
            const setName = row[0];
            const question = {
              id: generateId(),
              text: row[1],
              options: [
                row[2] || '',
                row[3] || '',
                row[4] || '',
                row[5] || ''
              ],
              correctIndex: ['A', 'B', 'C', 'D'].indexOf((row[6] || 'A').toUpperCase())
            };
            
            if (question.correctIndex === -1) {
              question.correctIndex = 0;
            }
            
            if (!sets[setName]) {
              sets[setName] = {
                id: generateId(),
                name: setName,
                questions: []
              };
            }
            sets[setName].questions.push(question);
          }
          
          // Create age group
          const ageGroup = {
            id: generateId(),
            name: sheetName,
            theme: theme,
            celebrationType: celebrationType,
            sets: Object.values(sets),
            roundRobinIndex: 0
          };
          
          if (ageGroup.sets.length > 0) {
            quiz.ageGroups.push(ageGroup);
          }
        });
        
        if (quiz.ageGroups.length === 0) {
          throw new Error('No valid age groups found in the file');
        }
        
        resolve(quiz);
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsArrayBuffer(file);
  });
}

/**
 * Generate a unique ID
 */
function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Validate quiz structure
 * @param {object} quiz - Quiz to validate
 * @returns {object} { valid: boolean, errors: string[] }
 */
export function validateQuiz(quiz) {
  const errors = [];
  
  if (!quiz.name || quiz.name.trim() === '') {
    errors.push('Quiz name is required');
  }
  
  if (!quiz.ageGroups || quiz.ageGroups.length === 0) {
    errors.push('At least one age group is required');
  }
  
  quiz.ageGroups?.forEach((ag, agIndex) => {
    if (!ag.name || ag.name.trim() === '') {
      errors.push(`Age group ${agIndex + 1}: Name is required`);
    }
    
    if (!ag.sets || ag.sets.length === 0) {
      errors.push(`Age group "${ag.name}": At least one question set is required`);
    }
    
    ag.sets?.forEach((set, setIndex) => {
      if (!set.questions || set.questions.length === 0) {
        errors.push(`Age group "${ag.name}", Set "${set.name}": At least one question is required`);
      }
      
      set.questions?.forEach((q, qIndex) => {
        if (!q.text || q.text.trim() === '') {
          errors.push(`Age group "${ag.name}", Set "${set.name}", Question ${qIndex + 1}: Question text is required`);
        }
        
        const filledOptions = q.options?.filter(o => o && o.trim() !== '') || [];
        if (filledOptions.length < 2) {
          errors.push(`Age group "${ag.name}", Set "${set.name}", Question ${qIndex + 1}: At least 2 options are required`);
        }
      });
    });
  });
  
  return {
    valid: errors.length === 0,
    errors
  };
}
